#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Arena/UmbrellaArena.h"
#include "Components/CapsuleComponent.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaGameMode.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Flow/FlowRules.h"
#include "Flow/UmbrellaPlayerController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/WorldSettings.h"
#include "Health/UmbrellaHealthComponent.h"
#include "Input/EllaInputAdapterComponent.h"
#include "Level/LevelCatalogue.h"
#include "Level/LevelPlan.h"
#include "Level/UmbrellaLevelDirector.h"

namespace
{
	/** A ticking game world with the Umbrella game mode and one flow controller, as the menu starts it. */
	struct FRouteWalkerWorld
	{
		UWorld* World = nullptr;
		UGameInstance* Instance = nullptr;
		AUmbrellaPlayerController* Controller = nullptr;

		FRouteWalkerWorld()
		{
			World = UWorld::CreateWorld(EWorldType::Game, false);
			FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
			Context.SetCurrentWorld(World);
			Instance = NewObject<UGameInstance>(GEngine);
			Instance->AddToRoot();
			Context.OwningGameInstance = Instance;
			World->SetGameInstance(Instance);
			World->GetWorldSettings()->DefaultGameMode = AUmbrellaGameMode::StaticClass();
			World->SetGameMode(FURL());
			World->InitializeActorsForPlay(FURL());
			World->BeginPlay();
			Controller = World->SpawnActor<AUmbrellaPlayerController>();
			Controller->PlayerState = World->SpawnActor<APlayerState>();
			Controller->KeepTutorialInMemoryOnly();
			Controller->MarkTutorialSeen();
		}

		~FRouteWalkerWorld()
		{
			// End play first (as UmbrellaTestWorld does): a long-ticked world torn down without EndPlay crashed the next
			// test's garbage collection (ABuoyancyManager destructor).
			for (TActorIterator<AActor> It(World); It; ++It)
			{
				It->RouteEndPlay(EEndPlayReason::Quit);
			}
			Controller->Player = nullptr;
			World->SetBegunPlay(false);
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
			Instance->RemoveFromRoot();
		}

		void Frame(float Delta)
		{
			++GFrameCounter;
			World->Tick(LEVELTICK_All, Delta);
		}
	};

	/** agentplay's `route N T 1` walker (JourneyHookSubsystem): D held, Space every 0.6 s, E every 0.9 s, J held while
	 *  Ella is 300 above the CP1 stand height, heal when hurt. Same numbers, through the input adapter's own handlers. */
	namespace RouteWalker
	{
		constexpr float HopSeconds = 0.6f;
		constexpr float DashSeconds = 0.9f;
		constexpr float TrimAbove = 300.0f;
		constexpr float Timeout = 60.0f;
		constexpr float StallX = 11465.0f;
		/** A player who sinks under the slot-5 (07A) low solid into its bypass lane: J held above this height. */
		constexpr float BypassTrimZ = 200.0f;
		/** B12: where agentplay's CP0 -> CP1 step began on 7851afd0 (after 8 s untrimmed and 20 s idle: at the route
		 *  ceiling), and where its walker then stood for 40 s. Z sits 6 units under the ceiling line (1 036): the line itself
		 *  is lethal since D-new-ceiling-lethal, so the walker starts just under it. */
		constexpr float B12StartX = 974.0f;
		constexpr float B12StartZ = 1030.0f;
		constexpr float B12StallX = 1903.0f;
	}
}

/** Walks FromCp -> FromCp + 1 with agentplay's real-key walker inputs, J held while Ella is above TrimZ. Returns Ella's best
 *  X and the checkpoint reached. bGameMovement: put the character movement in the mode the game's possession leaves it in.
 *  Start: Ella's start (zero: the checkpoint's stand); StallX: where the sweep looks for a solid at z 450. */
struct FRouteWalkResult
{
	float BestX = 0.0f;
	int32 Checkpoint = 0;
	int32 MovementMode = -1;
	float StopX = 0.0f;
	bool bLocal = false;
	bool bSolidAhead = false;
	float SolidFaceX = 0.0f;
	FString Slot5;
	FString StallSlot;
	FString BlockAhead;
	float RightWallInnerX = 0.0f;
	FBox SolidBox = FBox(ForceInit);
};

static FRouteWalkResult RouteWalkerStep(FAutomationTestBase& T, float Delta, float TrimZOverride, bool bGameMovement, int32 FromCp,
	FVector Start, float StallX)
{
	FRouteWalkResult Result;
	FRouteWalkerWorld Test;
	Test.Controller->StartDirectorsCut();
	AUmbrellaGameMode* Mode = Test.World->GetAuthGameMode<AUmbrellaGameMode>();
	AUmbrellaLevelDirector* Level = Mode ? Mode->GetLevelDirector() : nullptr;
	AEllaCharacter* Ella = Cast<AEllaCharacter>(Test.Controller->GetPawn());
	if (!T.TestNotNull(TEXT("route built"), Level) || !T.TestNotNull(TEXT("Ella"), Ella))
	{
		return Result;
	}
	// The game possesses Ella through the player controller, and ACharacter::Restart (Engine Character.cpp:1388) calls
	// SetDefaultMovementMode after the motor's BeginPlay set MOVE_None: measured in the game, mode 3 (Falling), so the
	// character movement's swept move stops Ella at solids. This transient world's controller does not restart the pawn.
	// The character movement only runs its swept move for a locally controlled pawn; with no net driver UE 5.8 counts a
	// player controller as local only when it has a ULocalPlayer (PlayerController.cpp:332), as the game's does.
	if (bGameMovement)
	{
		Test.Controller->Player = NewObject<ULocalPlayer>(GEngine);
		Ella->GetCharacterMovement()->SetDefaultMovementMode();
	}
	Result.MovementMode = static_cast<int32>(Ella->GetCharacterMovement()->MovementMode.GetValue());
	Result.bLocal = Ella->IsLocallyControlled();
	{
		// The cause in the world: slot 5 is 07A and a capsule sweep at the walker's height meets a route solid at its face.
		FHitResult Hit;
		FCollisionQueryParams Query;
		Query.AddIgnoredActor(Ella);
		const FVector From(StallX - 25.0f, Ella->GetActorLocation().Y, 450.0f);
		Result.bSolidAhead = Test.World->SweepSingleByChannel(Hit, From, From + FVector(50.0f, 0.0f, 0.0f), FQuat::Identity,
			Ella->GetCapsuleComponent()->GetCollisionObjectType(), Ella->GetCapsuleComponent()->GetCollisionShape(), Query)
			&& Level->GetSpawned().Contains(Hit.GetActor());
		Result.SolidFaceX = Result.bSolidAhead ? static_cast<float>(Hit.Location.X) : 0.0f;
		if (Result.bSolidAhead)
		{
			Result.SolidBox = Hit.GetActor()->GetComponentsBoundingBox(true);
			T.AddInfo(FString::Printf(TEXT("SOLID %s x %.0f..%.0f z %.0f..%.0f"), *Hit.GetActor()->GetName(), Result.SolidBox.Min.X,
				Result.SolidBox.Max.X, Result.SolidBox.Min.Z, Result.SolidBox.Max.Z));
		}
		const TArray<FChunkVariant>& Slots = Level->GetRoute().Slots;
		Result.Slot5 = Slots.IsValidIndex(5) ? Slots[5].Label() : FString();
		for (int32 Slot = 0; Slot < Slots.Num(); ++Slot)
		{
			if (StallX >= LevelCatalogue::SlotStartX(Slot))
			{
				Result.StallSlot = FString::Printf(TEXT("%d:%s"), Slot, *Slots[Slot].Label());
			}
		}
	}
	for (TActorIterator<AUmbrellaArena> It(Test.World); It; ++It)
	{
		Result.RightWallInnerX = It->GetRightWallInnerX();
	}
	// Where the walker's step began: Ella standing at the checkpoint, or the measured start.
	Ella->SetActorLocation(Start.IsZero() ? LevelPlan::CheckpointStandLocation(FromCp) : FVector(Start.X, Ella->GetActorLocation().Y, Start.Z));
	Ella->GetCharacterMovement()->Velocity = FVector::ZeroVector;
	Test.Frame(Delta);
	T.TestEqual(TEXT("start checkpoint reached"), Level->GetCheckpointReached(), FromCp);
	T.AddInfo(FString::Printf(TEXT("ROUTE %s"), *Level->GetRoute().Signature()));

	UEllaInputAdapterComponent* Input = Ella->GetInputAdapter();
	const float TrimZ = TrimZOverride > 0.0f ? TrimZOverride : static_cast<float>(LevelPlan::CheckpointStandLocation(1).Z) + RouteWalker::TrimAbove;
	Input->ApplyAxis(EUmbrellaInputAction::MoveX, 1.0f);
	float SinceHop = RouteWalker::HopSeconds;
	float SinceDash = RouteWalker::DashSeconds;
	float SinceLog = 0.0f;
	bool bSinking = false;
	float BestX = static_cast<float>(Ella->GetActorLocation().X);
	float Elapsed = 0.0f;
	int32 Heals = 0;
	int32 Cards = 0;
	float MinZPast = TNumericLimits<float>::Max();
	float MaxZPast = TNumericLimits<float>::Lowest();
	while (Elapsed < RouteWalker::Timeout && Level->GetCheckpointReached() < FromCp + 1)
	{
		const EFlowScreen Screen = Test.Controller->GetScreen();
		if (Screen != EFlowScreen::Playing)
		{
			// A level-up or story card: the walker presses Enter; a refuge purchase: Escape.
			++Cards;
			Test.Controller->ApplyCommand(Screen == EFlowScreen::Purchase ? EFlowCommand::Back : EFlowCommand::Continue);
		}
		SinceHop += Delta;
		SinceDash += Delta;
		SinceLog += Delta;
		if (SinceHop >= RouteWalker::HopSeconds)
		{
			SinceHop = 0.0f;
			Input->ApplyPress(EUmbrellaInputAction::Hop);
			Input->ApplyRelease(EUmbrellaInputAction::Hop);
		}
		if (SinceDash >= RouteWalker::DashSeconds)
		{
			SinceDash = 0.0f;
			Input->ApplyPress(EUmbrellaInputAction::DashForward);
			Input->ApplyRelease(EUmbrellaInputAction::DashForward);
		}
		const bool bHigh = Ella->GetActorLocation().Z > TrimZ;
		if (bHigh != bSinking)
		{
			bSinking = bHigh;
			bHigh ? Input->ApplyPress(EUmbrellaInputAction::Shoot) : Input->ApplyRelease(EUmbrellaInputAction::Shoot);
		}
		if (UUmbrellaHealthComponent* Health = Ella->GetHealth())
		{
			const FHealthState& S = Health->GetState();
			if (!S.IsDefeated() && (S.Active < S.Capacity || S.Lives < S.MaxLives))
			{
				Health->ResetForRetry();
				++Heals;
			}
		}
		Test.Frame(Delta);
		Elapsed += Delta;
		const FVector At = Ella->GetActorLocation();
		if (Elapsed > RouteWalker::Timeout - 5.0f && Result.StopX == 0.0f)
		{
			Result.StopX = static_cast<float>(At.X);
		}
		BestX = FMath::Max(BestX, static_cast<float>(At.X));
		if (At.X >= StallX - 200.0f && At.X <= StallX + 200.0f)
		{
			MinZPast = FMath::Min(MinZPast, static_cast<float>(At.Z));
			MaxZPast = FMath::Max(MaxZPast, static_cast<float>(At.Z));
		}
		if (SinceLog >= 5.0f)
		{
			SinceLog = 0.0f;
			T.AddInfo(FString::Printf(TEXT("WALK t=%.1f x=%.0f z=%.0f vx=%.0f vz=%.0f cp=%d"), Elapsed, At.X, At.Z,
				Ella->GetVelocity().X, Ella->GetVelocity().Z, Level->GetCheckpointReached()));
		}
	}
	{
		// What Ella's capsule meets just ahead of where the walk ended (B12 measured the arena's RightWall here).
		FCollisionQueryParams Query;
		Query.AddIgnoredActor(Ella);
		FHitResult Hit;
		const FVector From = Ella->GetActorLocation();
		if (Test.World->SweepSingleByChannel(Hit, From, From + FVector(5.0f, 0.0f, 0.0f), FQuat::Identity,
			Ella->GetCapsuleComponent()->GetCollisionObjectType(), Ella->GetCapsuleComponent()->GetCollisionShape(), Query) && Hit.GetComponent())
		{
			Result.BlockAhead = Hit.GetComponent()->GetName();
		}
		T.AddInfo(FString::Printf(TEXT("END ella=(%.1f,%.1f) block_ahead=%s"), From.X, From.Z, *Result.BlockAhead));
	}
	Input->ApplyAxis(EUmbrellaInputAction::MoveX, 0.0f);
	Input->ApplyRelease(EUmbrellaInputAction::Shoot);
	T.AddInfo(FString::Printf(TEXT("WALK_END t=%.1f best_x=%.0f cp=%d heals=%d cards=%d near_%.0f z=[%.0f,%.0f] trim_z=%.0f mode=%d"),
		Elapsed, BestX, Level->GetCheckpointReached(), Heals, Cards, StallX, MinZPast, MaxZPast, TrimZ, Result.MovementMode));
	Result.BestX = BestX;
	Result.Checkpoint = Level->GetCheckpointReached();
	return Result;
}

// B8 (agentplay playthrough): the real-key walker stops at x 11 465 between CP1 and CP2 on every Director's Cut run.
// Cause, measured: slot 5 of the Director's Cut route is 07A; its low solid spans x 11 482..11 674, z 367..518. The walker
// trims to the CP1 stand height + 300 (z ~450), inside that solid's height, so in the game's movement mode Ella's capsule
// (radius 17) rests on its face at x 11 464.5. Same inputs as the walker, same world.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelRouteWalkerStopsAt07ASolid, "UmbrellaElla.Level.World.RealInputWalkerAtZ450StopsAt07ALowSolid",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLevelRouteWalkerStopsAt07ASolid::RunTest(const FString& Parameters)
{
	const FRouteWalkResult R = RouteWalkerStep(*this, 1.0f / 60.0f, 0.0f, true, 1, FVector::ZeroVector, RouteWalker::StallX);
	TestEqual(TEXT("game movement mode (Falling)"), R.MovementMode, static_cast<int32>(MOVE_Falling));
	TestTrue(TEXT("Ella locally controlled, as in the game"), R.bLocal);
	TestEqual(TEXT("slot 5 is 07A"), R.Slot5, FString(TEXT("07A")));
	TestTrue(TEXT("a route solid ahead at the walker's height (z 450)"), R.bSolidAhead);
	TestEqual(TEXT("capsule stops at that solid's face"), R.SolidFaceX, 11464.5f, 1.0f);
	TestEqual(TEXT("stopped where agentplay's walker stopped (x 11 464.5)"), R.StopX, 11464.5f, 1.0f);
	TestEqual(TEXT("no CP2 at the walker's height"), R.Checkpoint, 1);
	return true;
}

// B8: not a soft-lock. The same real keys, but sinking (J held) to the 07A bypass lane under the low solid, reach CP2
// within the walker's 60 s budget in the game's movement mode.
#define UMBRELLAELLA_ROUTE_BYPASS_TEST(Fps) \
	IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelRouteBypass##Fps, "UmbrellaElla.Level.World.RealInputBypassUnder07ASolidReachesCP2At" #Fps "fps", \
		EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter) \
	bool FLevelRouteBypass##Fps::RunTest(const FString& Parameters) \
	{ \
		const FRouteWalkResult R = RouteWalkerStep(*this, 1.0f / Fps, RouteWalker::BypassTrimZ, true, 1, FVector::ZeroVector, RouteWalker::StallX); \
		TestEqual(TEXT("game movement mode (Falling)"), R.MovementMode, static_cast<int32>(MOVE_Falling)); \
		TestTrue(TEXT("Ella locally controlled, as in the game"), R.bLocal); \
		TestTrue(TEXT("past the 07A low solid"), R.BestX > 11674.0f); \
		TestEqual(TEXT("CP2 reached with real inputs within 60 s"), R.Checkpoint, 2); \
		return true; \
	}
UMBRELLAELLA_ROUTE_BYPASS_TEST(60)
UMBRELLAELLA_ROUTE_BYPASS_TEST(120)

// B12 (agentplay 67011eb2): the real-key walker stood at x 1 903 (z ~450) for 40 s between CP0 and CP1. Cause, measured:
// slot 0 is 01B and has no solid there; the arena's own RightWall (inner face x 1 920, z -100..1 180) stood at the arena's
// home width on the route. Before move's B7 ceiling (z <= 1 036) Ella flew over it; now every player meets it. Fix: the
// route moves that wall to the route end (AUmbrellaLevelDirector::BuildRouteFrom). Same start as agentplay's step (x 974,
// at the ceiling), the walker's own numbers and trim, the game's movement mode.
#define UMBRELLAELLA_ROUTE_CP0_TEST(Fps) \
	IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelRouteCp0Ceiling##Fps, "UmbrellaElla.Level.World.RealInputWalkerFromCeilingReachesCP1At" #Fps "fps", \
		EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter) \
	bool FLevelRouteCp0Ceiling##Fps::RunTest(const FString& Parameters) \
	{ \
		const FRouteWalkResult R = RouteWalkerStep(*this, 1.0f / Fps, 0.0f, true, 0, \
			FVector(RouteWalker::B12StartX, 0.0f, RouteWalker::B12StartZ), RouteWalker::B12StallX); \
		TestEqual(TEXT("game movement mode (Falling)"), R.MovementMode, static_cast<int32>(MOVE_Falling)); \
		TestTrue(TEXT("Ella locally controlled, as in the game"), R.bLocal); \
		TestEqual(TEXT("x 1 903 is in slot 0 (01B)"), R.StallSlot, FString(TEXT("0:01B"))); \
		TestFalse(TEXT("no route solid at the walker's height at x 1 903"), R.bSolidAhead); \
		TestEqual(TEXT("arena right wall at the route end on the route"), R.RightWallInnerX, LevelCatalogue::RouteLength(), 0.5f); \
		TestTrue(TEXT("past x 1 920 (the arena's home right edge)"), R.BestX > 1920.0f); \
		TestEqual(TEXT("CP1 reached with real inputs within 60 s"), R.Checkpoint, 1); \
		return true; \
	}
UMBRELLAELLA_ROUTE_CP0_TEST(60)
UMBRELLAELLA_ROUTE_CP0_TEST(120)

// B12: the route's right wall is the route end only while the route runs: back at the arena edge after the Keeper handoff
// moves the arena and after ClearRoute.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelRouteRightWallSpan, "UmbrellaElla.Level.World.RouteRightWallAtRouteEndThenArenaEdge",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLevelRouteRightWallSpan::RunTest(const FString& Parameters)
{
	FRouteWalkerWorld Test;
	AUmbrellaGameMode* Mode = Test.World->GetAuthGameMode<AUmbrellaGameMode>();
	if (!TestNotNull(TEXT("game mode"), Mode))
	{
		return false;
	}
	Test.Controller->StartDirectorsCut();
	AUmbrellaArena* Arena = Mode->GetArena();
	AUmbrellaLevelDirector* Level = Mode->GetLevelDirector();
	AEllaCharacter* Ella = Cast<AEllaCharacter>(Test.Controller->GetPawn());
	if (!TestNotNull(TEXT("arena"), Arena) || !TestNotNull(TEXT("route"), Level) || !TestNotNull(TEXT("Ella"), Ella))
	{
		return false;
	}
	const float Width = GetDefault<UUmbrellaTuning>()->ArenaCamera.ArenaWidth;
	const float Home = static_cast<float>(Arena->GetActorLocation().X);
	TestEqual(TEXT("route: right wall at the route end"), Arena->GetRightWallInnerX(), LevelCatalogue::RouteLength(), 0.5f);
	TestTrue(TEXT("route end past the handoff line"), LevelCatalogue::RouteLength() > LevelPlan::KeeperHandoffX());
	Ella->SetActorLocation(LevelPlan::CheckpointStandLocation(3) + FVector(LevelPlan::KeeperHandoffX() - LevelPlan::CheckpointStandLocation(3).X + 10.0f, 0.0, 0.0));
	Test.Frame(1.0f / 60.0f);
	TestTrue(TEXT("handed off"), Level->HasHandedOff());
	TestEqual(TEXT("fight: right wall at the moved arena's edge"), Arena->GetRightWallInnerX(),
		static_cast<float>(LevelPlan::KeeperArenaOrigin().X) + Width, 0.5f);
	Level->ClearRoute();
	TestEqual(TEXT("after ClearRoute: right wall at the arena width"), Arena->GetRightWallInnerX(), Home + Width, 0.5f);
	return true;
}

#endif

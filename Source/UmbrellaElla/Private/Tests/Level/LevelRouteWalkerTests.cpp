#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Components/CapsuleComponent.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaGameMode.h"
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
	}
}

/** Walks CP1 -> CP2 with agentplay's real-key walker inputs, J held while Ella is above TrimZ. Returns Ella's best X and
 *  the checkpoint reached. bGameMovement: put the character movement in the mode the game's possession leaves it in. */
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
};

static FRouteWalkResult RouteWalkerCp1ToCp2(FAutomationTestBase& T, float Delta, float TrimZOverride, bool bGameMovement)
{
	using namespace RouteWalker;
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
		Result.Slot5 = Level->GetRoute().Slots.IsValidIndex(5) ? Level->GetRoute().Slots[5].Label() : FString();
	}
	// Where the walker's CP1 -> CP2 step began: Ella standing at CP1.
	Ella->SetActorLocation(LevelPlan::CheckpointStandLocation(1));
	Test.Frame(Delta);
	T.TestEqual(TEXT("CP1 reached"), Level->GetCheckpointReached(), 1);
	T.AddInfo(FString::Printf(TEXT("ROUTE %s"), *Level->GetRoute().Signature()));

	UEllaInputAdapterComponent* Input = Ella->GetInputAdapter();
	const float TrimZ = TrimZOverride > 0.0f ? TrimZOverride : static_cast<float>(LevelPlan::CheckpointStandLocation(1).Z) + TrimAbove;
	Input->ApplyAxis(EUmbrellaInputAction::MoveX, 1.0f);
	float SinceHop = HopSeconds;
	float SinceDash = DashSeconds;
	float SinceLog = 0.0f;
	bool bSinking = false;
	float BestX = static_cast<float>(Ella->GetActorLocation().X);
	float Elapsed = 0.0f;
	int32 Heals = 0;
	int32 Cards = 0;
	float MinZPast = TNumericLimits<float>::Max();
	float MaxZPast = TNumericLimits<float>::Lowest();
	while (Elapsed < Timeout && Level->GetCheckpointReached() < 2)
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
		if (SinceHop >= HopSeconds)
		{
			SinceHop = 0.0f;
			Input->ApplyPress(EUmbrellaInputAction::Hop);
			Input->ApplyRelease(EUmbrellaInputAction::Hop);
		}
		if (SinceDash >= DashSeconds)
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
		if (Elapsed > Timeout - 5.0f && Result.StopX == 0.0f)
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
	const FRouteWalkResult R = RouteWalkerCp1ToCp2(*this, 1.0f / 60.0f, 0.0f, true);
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
#define ROUTE_BYPASS_TEST(Fps) \
	IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelRouteBypass##Fps, "UmbrellaElla.Level.World.RealInputBypassUnder07ASolidReachesCP2At" #Fps "fps", \
		EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter) \
	bool FLevelRouteBypass##Fps::RunTest(const FString& Parameters) \
	{ \
		const FRouteWalkResult R = RouteWalkerCp1ToCp2(*this, 1.0f / Fps, RouteWalker::BypassTrimZ, true); \
		TestEqual(TEXT("game movement mode (Falling)"), R.MovementMode, static_cast<int32>(MOVE_Falling)); \
		TestTrue(TEXT("Ella locally controlled, as in the game"), R.bLocal); \
		TestTrue(TEXT("past the 07A low solid"), R.BestX > 11674.0f); \
		TestEqual(TEXT("CP2 reached with real inputs within 60 s"), R.Checkpoint, 2); \
		return true; \
	}
ROUTE_BYPASS_TEST(60)
ROUTE_BYPASS_TEST(120)

#endif

#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Projectile/UmbrellaShotSpec.h"
#include "Story/StoryRules.h"
#include "Story/StorySubsystem.h"

// Lead order Nov 13 (agentplay playthrough): Journey Complete showed "Shots fired 0" after ~45 s of J held. Shots go
// through the one projectile service, whose ProjectileSpawned event names the shot kind; the run statistics must count
// the player's shots from that real event, not from a hand-made one.
namespace ProgressionJourneyShotTest
{
	AUmbrellaProjectile* FireKind(UWorld* World, EUmbrellaShotKind Kind, float OffsetX)
	{
		FUmbrellaShotSpec Spec;
		Spec.Kind = Kind;
		Spec.Origin = FVector(OffsetX, 0.0, 0.0);
		Spec.Radius = 8.0f;
		Spec.Damage = 1.0f;
		Spec.LifetimeSeconds = 2.0f;
		Spec.SourceId = FName(TEXT("ProgressionShotStatsTest"));
		return AUmbrellaProjectile::Fire(World, Spec);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgressionJourneyShotStats, "UmbrellaElla.Progression.World.JourneyStatsCountPlayerShots",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProgressionJourneyShotStats::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World);
	UStorySubsystem* Story = World->GetSubsystem<UStorySubsystem>();
	const bool bOk = TestNotNull(TEXT("bus"), Bus) && TestNotNull(TEXT("story subsystem"), Story);
	if (bOk)
	{
		FUmbrellaEvent Mode;
		Mode.Type = EUmbrellaEventType::ModeSelected;
		Mode.Detail = FName(TEXT("DirectorsCut"));
		Bus->Broadcast(Mode);
		const int32 PlayerShots = 3;
		// Spaced apart so no shot touches another; nothing else is in the world to hit.
		const float Spacing = 1000.0f;
		for (int32 Index = 0; Index < PlayerShots; ++Index)
		{
			TestNotNull(TEXT("player shot fired"), ProgressionJourneyShotTest::FireKind(World, EUmbrellaShotKind::PlayerBlast, Spacing * Index));
		}
		TestNotNull(TEXT("red shot fired"), ProgressionJourneyShotTest::FireKind(World, EUmbrellaShotKind::EnemyRed, -Spacing));
		const FStoryRunStats& Stats = Story->GetModel().GetStats();
		TestEqual(TEXT("Shots fired counts the player's shots from the projectile service's event"), Stats.ShotsFired, PlayerShots);
		TestEqual(TEXT("Shots fired at you counts only the enemy shot"), Stats.ShotsFiredAtYou, 1);
		const TArray<TPair<FString, FString>> Rows = StoryStatsRows(Stats);
		const int32 ShotsRow = 4;
		TestTrue(TEXT("Journey Complete row 5 is Shots fired"), Rows.IsValidIndex(ShotsRow) && Rows[ShotsRow].Key == TEXT("Shots fired"));
		TestTrue(TEXT("Journey Complete shows the player's shots"), Rows.IsValidIndex(ShotsRow) && Rows[ShotsRow].Value == FString::FromInt(PlayerShots));
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return bOk;
}

#endif

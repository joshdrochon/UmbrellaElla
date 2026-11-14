#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Components/AudioComponent.h"
#include "Feedback/Audio/UmbrellaCueSubsystem.h"
#include "Feedback/Audio/UmbrellaCueTable.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Sound/SoundWave.h"
#include "Misc/AutomationTest.h"
#include "Core/UmbrellaEventBus.h"
#include "Projectile/UmbrellaShotSpec.h"
#include "UObject/UObjectIterator.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAudioCueMusicCue, "UmbrellaElla.Audio.MusicCueIsLooped",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FAudioCueMusicCue::RunTest(const FString& Parameters)
{
	TestTrue(TEXT("StartMusic is music"), UUmbrellaCueSubsystem::IsMusicCue(TEXT("StartMusic")));
	TestFalse(TEXT("Shot is a one-shot"), UUmbrellaCueSubsystem::IsMusicCue(TEXT("Shot")));
	TestFalse(TEXT("EndMusic is a sting"), UUmbrellaCueSubsystem::IsMusicCue(TEXT("EndMusic")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAudioCueMusicRestart, "UmbrellaElla.Audio.World.MusicRestartReusesOneComponent",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FAudioCueMusicRestart::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	UUmbrellaCueSubsystem* Cues = World->GetSubsystem<UUmbrellaCueSubsystem>();
	if (TestNotNull(TEXT("cue subsystem"), Cues))
	{
		USoundWave* Wave = NewObject<USoundWave>(GetTransientPackage());
		Cues->RestartMusic(Wave);
		UAudioComponent* First = Cues->GetMusicComponent();
		const int32 FirstStarts = Cues->GetMusicStartCount();
		Cues->RestartMusic(Wave);
		TestTrue(TEXT("mode change reuses the same component (or none without an audio device)"), Cues->GetMusicComponent() == First);
		TestEqual(TEXT("each restart is counted once"), Cues->GetMusicStartCount(), First ? FirstStarts + 1 : 0);
		Cues->StopMusic();
		if (First)
		{
			TestFalse(TEXT("stopped music is not playing"), First->IsPlaying());
			TestTrue(TEXT("component is kept for the next mode"), IsValid(First));
		}
		Cues->RestartMusic(nullptr);
		TestEqual(TEXT("null sound only stops"), Cues->GetMusicStartCount(), First ? FirstStarts + 1 : 0);
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

namespace
{
	FUmbrellaEvent CueTestEvent(EUmbrellaEventType Type, const TCHAR* Detail, const TCHAR* Target = TEXT(""))
	{
		FUmbrellaEvent Event;
		Event.Type = Type;
		Event.Detail = FName(Detail);
		Event.TargetId = FName(Target);
		return Event;
	}

	bool CueTestPlays(const FUmbrellaEvent& Event, const TCHAR* Id, FName Prev = NAME_None)
	{
		for (const FUmbrellaSoundCue* Row : UmbrellaCueTable::ForEvent(Event, Prev))
		{
			if (FName(Row->Id) == FName(Id))
			{
				return true;
			}
		}
		return false;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAudioCueEveryListedSound, "UmbrellaElla.Audio.EveryListedSoundHasACueMapping",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FAudioCueEveryListedSound::RunTest(const FString& Parameters)
{
	// pipeline/audio/sound-list.csv: id,family,kind,class,channels,takes,pitch_jitter,gdd,tier,... (13 rows are cut).
	FString Csv;
	const FString Path = FPaths::Combine(FPaths::ProjectDir(), TEXT("pipeline/audio/sound-list.csv"));
	if (!FFileHelper::LoadFileToString(Csv, *Path))
	{
		AddWarning(TEXT("sound-list.csv not found next to the project; the python test covers the same table"));
		return true;
	}
	TArray<FString> Lines;
	Csv.ParseIntoArrayLines(Lines);
	int32 Checked = 0;
	for (int32 Index = 1; Index < Lines.Num(); ++Index)
	{
		TArray<FString> Cells;
		Lines[Index].ParseIntoArray(Cells, TEXT(","), false);
		if (Cells.Num() < 9 || Cells[8] == TEXT("cut"))
		{
			continue;
		}
		const FUmbrellaSoundCue* Row = UmbrellaCueTable::Find(FName(*Cells[0]));
		if (TestNotNull(*FString::Printf(TEXT("%s has a cue mapping"), *Cells[0]), Row) && Row)
		{
			TestEqual(*FString::Printf(TEXT("%s loops like the list says"), *Cells[0]), Row->bLoop, Cells[2] == TEXT("loop"));
			TestEqual(*FString::Printf(TEXT("%s takes"), *Cells[0]), Row->Takes, FCString::Atoi(*Cells[5]));
		}
		++Checked;
	}
	TestTrue(TEXT("read the live rows"), Checked > 100);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAudioCueRouting, "UmbrellaElla.Audio.BusEventsRouteToTheirSounds",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FAudioCueRouting::RunTest(const FString& Parameters)
{
	TestTrue(TEXT("player blast plays WandBolt"), CueTestPlays(CueTestEvent(EUmbrellaEventType::ProjectileSpawned, TEXT("PlayerBlast")), TEXT("WandBolt")));
	TestFalse(TEXT("player blast does not play the red launch"), CueTestPlays(CueTestEvent(EUmbrellaEventType::ProjectileSpawned, TEXT("PlayerBlast")), TEXT("OwlBoltLaunch")));
	TestTrue(TEXT("red shot plays OwlBoltLaunch"), CueTestPlays(CueTestEvent(EUmbrellaEventType::ProjectileSpawned, TEXT("EnemyRed")), TEXT("OwlBoltLaunch")));
	TestTrue(TEXT("yellow shot plays KeeperYellowLaunch"), CueTestPlays(CueTestEvent(EUmbrellaEventType::ProjectileSpawned, TEXT("EnemyYellow")), TEXT("KeeperYellowLaunch")));
	TestTrue(TEXT("wing hit"), CueTestPlays(CueTestEvent(EUmbrellaEventType::BossTargetHit, TEXT("wings"), TEXT("WINGS")), TEXT("HitWing")));
	TestTrue(TEXT("mechanism hit is metal"), CueTestPlays(CueTestEvent(EUmbrellaEventType::BossTargetHit, TEXT("mechanisms"), TEXT("MECH_REAR")), TEXT("HitOwl")));
	TestTrue(TEXT("clock hit is glass"), CueTestPlays(CueTestEvent(EUmbrellaEventType::BossTargetHit, TEXT("clock"), TEXT("CLOCK")), TEXT("HitClock")));
	TestTrue(TEXT("enemy equipment hit"), CueTestPlays(CueTestEvent(EUmbrellaEventType::BossTargetHit, TEXT("Enemy")), TEXT("HitEnemy")));
	TestTrue(TEXT("gust windup"), CueTestPlays(CueTestEvent(EUmbrellaEventType::BossAttackTelegraphed, TEXT("GUST_Band")), TEXT("GustWindup")));
	TestTrue(TEXT("cast warning"), CueTestPlays(CueTestEvent(EUmbrellaEventType::BossAttackTelegraphed, TEXT("MECH_Middle_Curve")), TEXT("CastWarning")));
	TestTrue(TEXT("damage plays PlayerHurt"), CueTestPlays(CueTestEvent(EUmbrellaEventType::PlayerHealthChanged, TEXT("Damage")), TEXT("PlayerHurt")));
	TestFalse(TEXT("a heal is not a hurt"), CueTestPlays(CueTestEvent(EUmbrellaEventType::PlayerHealthChanged, TEXT("Heal")), TEXT("PlayerHurt")));
	TestTrue(TEXT("a heal plays ShieldHeal"), CueTestPlays(CueTestEvent(EUmbrellaEventType::PlayerHealthChanged, TEXT("Heal")), TEXT("ShieldHeal")));
	TestTrue(TEXT("defeat plays the sting"), CueTestPlays(CueTestEvent(EUmbrellaEventType::PlayerDefeated, TEXT("")), TEXT("FailSting")));
	TestTrue(TEXT("catch"), CueTestPlays(CueTestEvent(EUmbrellaEventType::CatchSucceeded, TEXT("")), TEXT("ShieldCatch")));
	TestTrue(TEXT("canopy opens on Rise"), CueTestPlays(CueTestEvent(EUmbrellaEventType::UmbrellaConfigChanged, TEXT("Rise")), TEXT("UmbrellaOpen")));
	TestFalse(TEXT("a spell equip plays no canopy sound"), CueTestPlays(CueTestEvent(EUmbrellaEventType::UmbrellaConfigChanged, TEXT("StreamedBlast")), TEXT("UmbrellaOpen")));
	TestTrue(TEXT("absorb stops when the canopy leaves AbsorbFall"), CueTestPlays(CueTestEvent(EUmbrellaEventType::UmbrellaConfigChanged, TEXT("Rise")), TEXT("AbsorbStop"), TEXT("AbsorbFall")));
	TestFalse(TEXT("no absorb stop when it was not absorbing"), CueTestPlays(CueTestEvent(EUmbrellaEventType::UmbrellaConfigChanged, TEXT("Rise")), TEXT("AbsorbStop"), TEXT("ShootFall")));
	TestTrue(TEXT("the wind loop stops when the current is left"), UmbrellaCueTable::GroupStops().ContainsByPredicate([](const FUmbrellaLoopGroupStop& Stop) { return Stop.Event == EUmbrellaEventType::WindExited; }));
	return true;
}

namespace
{
	/** The Detail the projectile service really stamps on ProjectileSpawned (UmbrellaProjectile.cpp). */
	FName CueTestShotDetail(EUmbrellaShotKind Kind)
	{
		return StaticEnum<EUmbrellaShotKind>()->GetNameByValue(static_cast<int64>(Kind));
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAudioCueRealShotDetail, "UmbrellaElla.Audio.RealShotEventsRouteToTheirRows",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FAudioCueRealShotDetail::RunTest(const FString& Parameters)
{
	// The game sends "EUmbrellaShotKind::EnemyRed", not "EnemyRed": the row must still match, or the shot falls back
	// to the flat placeholder that has no concurrency limit.
	FUmbrellaEvent Event;
	Event.Type = EUmbrellaEventType::ProjectileSpawned;
	Event.Detail = CueTestShotDetail(EUmbrellaShotKind::EnemyRed);
	TestTrue(TEXT("real red shot plays OwlBoltLaunch"), CueTestPlays(Event, TEXT("OwlBoltLaunch")));
	Event.Detail = CueTestShotDetail(EUmbrellaShotKind::EnemyYellow);
	TestTrue(TEXT("real yellow shot plays KeeperYellowLaunch"), CueTestPlays(Event, TEXT("KeeperYellowLaunch")));
	Event.Detail = CueTestShotDetail(EUmbrellaShotKind::PlayerBlast);
	TestTrue(TEXT("real player blast plays WandBolt"), CueTestPlays(Event, TEXT("WandBolt")));
	TestEqual(TEXT("a plain detail is kept"), UmbrellaCueTable::CueDetail(TEXT("Rise")), FName(TEXT("Rise")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAudioCueNoFlatShots, "UmbrellaElla.Audio.World.KeeperVolleyPlaysNoFlatPlaceholder",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FAudioCueNoFlatShots::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	UUmbrellaCueSubsystem* Cues = World->GetSubsystem<UUmbrellaCueSubsystem>();
	UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World);
	if (TestNotNull(TEXT("cue subsystem"), Cues) && TestNotNull(TEXT("bus"), Bus))
	{
		// A Keeper volley as the game sends it: 12 shots, each with the projectile service's Detail.
		constexpr int32 Shots = 12;
		for (int32 Index = 0; Index < Shots; ++Index)
		{
			FUmbrellaEvent Event;
			Event.Type = EUmbrellaEventType::ProjectileSpawned;
			Event.Detail = CueTestShotDetail(Index % 2 ? EUmbrellaShotKind::EnemyYellow : EUmbrellaShotKind::EnemyRed);
			Bus->Broadcast(Event);
		}
		TestEqual(TEXT("no shot plays the flat placeholder (no class, no concurrency)"), Cues->GetFlatCueCount(), 0);
		TestEqual(TEXT("every shot plays its sound-list row"), Cues->GetSoundCueCount(), Shots);
		TestEqual(TEXT("the last shot is the yellow launch"), Cues->GetLastSoundId(), FName(TEXT("KeeperYellowLaunch")));
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAudioCueLoopReplay, "UmbrellaElla.Audio.World.LoopStartedTwicePlaysOnce",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FAudioCueLoopReplay::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	UUmbrellaCueSubsystem* Cues = World->GetSubsystem<UUmbrellaCueSubsystem>();
	if (TestNotNull(TEXT("cue subsystem"), Cues))
	{
		TestEqual(TEXT("no loop runs before any event"), Cues->GetPlayingLoopCount(), 0);
		int32 Before = 0;
		for (TObjectIterator<UAudioComponent> It; It; ++It)
		{
			Before += It->GetWorld() == World && It->IsPlaying() ? 1 : 0;
		}
		Cues->PlaySoundById(TEXT("OwlWingLoop"));
		Cues->PlaySoundById(TEXT("OwlWingLoop"));
		int32 Playing = 0;
		for (TObjectIterator<UAudioComponent> It; It; ++It)
		{
			Playing += It->GetWorld() == World && It->IsPlaying() ? 1 : 0;
		}
		TestTrue(TEXT("a loop started twice plays one copy"), Playing - Before <= 1);
		TestTrue(TEXT("at most one loop is tracked"), Cues->GetPlayingLoopCount() <= 1);
		Cues->StopLoop(TEXT("OwlWingLoop"));
		TestEqual(TEXT("stopping the loop leaves none"), Cues->GetPlayingLoopCount(), 0);
		if (Playing == Before)
		{
			AddInfo(TEXT("no audio device in this run: components are not created, the counts are trivially met"));
		}
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

#endif

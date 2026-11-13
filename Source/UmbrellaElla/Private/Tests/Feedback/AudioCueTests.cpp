#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Components/AudioComponent.h"
#include "Feedback/Audio/UmbrellaCueSubsystem.h"
#include "Feedback/Audio/UmbrellaCueTable.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Sound/SoundWave.h"
#include "Misc/AutomationTest.h"

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

#endif

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Components/AudioComponent.h"
#include "Feedback/Audio/UmbrellaCueSubsystem.h"
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

#endif

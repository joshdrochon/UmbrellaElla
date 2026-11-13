#include "Core/UmbrellaGameMode.h"
#include "Arena/UmbrellaArena.h"
#include "Core/EllaCharacter.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "EngineUtils.h"
#include "Flow/UmbrellaPlayerController.h"
#include "Level/UmbrellaLevelDirector.h"
#include "UI/UmbrellaHUD.h"

AUmbrellaGameMode::AUmbrellaGameMode()
{
	DefaultPawnClass = AEllaCharacter::StaticClass();
	PlayerControllerClass = AUmbrellaPlayerController::StaticClass();
	HUDClass = AUmbrellaHUD::StaticClass();
}

bool AUmbrellaGameMode::PlayerCanRestart_Implementation(APlayerController* Player)
{
	return bFightStarted && Super::PlayerCanRestart_Implementation(Player);
}

AUmbrellaArena* AUmbrellaGameMode::FindOrSpawnArena()
{
	if (Arena)
	{
		return Arena;
	}
	TActorIterator<AUmbrellaArena> Existing(GetWorld());
	if (Existing)
	{
		Arena = *Existing;
		return Arena;
	}
	Arena = GetWorld()->SpawnActor<AUmbrellaArena>(FVector::ZeroVector, FRotator::ZeroRotator);
	return Arena;
}

void AUmbrellaGameMode::EnsurePlayerPawn(APlayerController* Player)
{
	AUmbrellaArena* PlayArena = FindOrSpawnArena();
	if (!Player || !PlayArena)
	{
		return;
	}
	if (!Player->GetPawn())
	{
		RestartPlayerAtTransform(Player, FTransform(FRotator::ZeroRotator, PlayArena->GetPlayerStartLocation()));
	}
	Player->SetViewTarget(PlayArena);
}

void AUmbrellaGameMode::BeginFight(APlayerController* Player)
{
	bFightStarted = true;
	EnsurePlayerPawn(Player);
	if (UEncounterDirectorSubsystem* Director = GetWorld()->GetSubsystem<UEncounterDirectorSubsystem>())
	{
		Director->BeginKeeperFight();
	}
}

bool AUmbrellaGameMode::HasRoute() const
{
	return LevelDirector && LevelDirector->GetSlotsSpawned() > 0;
}

void AUmbrellaGameMode::BeginRoute(APlayerController* Player, int64 Seed)
{
	if (!Player || !GetWorld())
	{
		return;
	}
	if (!LevelDirector)
	{
		LevelDirector = GetWorld()->SpawnActor<AUmbrellaLevelDirector>();
	}
	if (!LevelDirector || LevelDirector->BuildRoute(Seed) <= 0)
	{
		return;
	}
	bFightStarted = true;
	EnsurePlayerPawn(Player);
	LevelDirector->SetArena(FindOrSpawnArena());
	LevelDirector->PlaceAtCheckpoint(Player->GetPawn(), 1);
}

void AUmbrellaGameMode::PlaceAtLastCheckpoint(APlayerController* Player)
{
	// After the Keeper handoff the encounter's own retry checkpoint decides where Ella stands.
	if (LevelDirector && Player && !LevelDirector->HasHandedOff())
	{
		LevelDirector->PlaceAtCheckpoint(Player->GetPawn(), FMath::Max(1, LevelDirector->GetCheckpointReached()));
	}
}

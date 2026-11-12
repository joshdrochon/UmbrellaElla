#include "Core/UmbrellaGameMode.h"
#include "Arena/UmbrellaArena.h"
#include "Core/EllaCharacter.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "EngineUtils.h"
#include "Flow/UmbrellaPlayerController.h"
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

#include "Owl/KeeperPartComponent.h"

#include "Core/UmbrellaCollision.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "Owl/KeeperLook.h"
#include "Engine/World.h"

UKeeperPartComponent::UKeeperPartComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	SetCollisionEnabled(ECollisionEnabled::NoCollision);
	SetCollisionObjectType(ECC_WorldDynamic);
	SetCollisionResponseToAllChannels(ECR_Ignore);
	SetCollisionResponseToChannel(UmbrellaCollision::PlayerShot, ECR_Block);
	SetGenerateOverlapEvents(true);
	SetCanEverAffectNavigation(false);
}

void UKeeperPartComponent::Configure(EKeeperPart InPart, const FVector2D& HalfExtent)
{
	PartId = InPart;
	SetBoxExtent(FVector(HalfExtent.X, KeeperLook::PartShotHalfDepth, HalfExtent.Y));
}

void UKeeperPartComponent::SetHittable(bool bHittable)
{
	SetCollisionEnabled(bHittable ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
}

EUmbrellaShotResult UKeeperPartComponent::ReceiveShot(const FUmbrellaShotSpec& Shot, const FVector& HitLocation)
{
	if (Shot.Kind != EUmbrellaShotKind::PlayerBlast)
	{
		return EUmbrellaShotResult::Ignored;
	}
	UWorld* World = GetWorld();
	UEncounterDirectorSubsystem* Director = World ? World->GetSubsystem<UEncounterDirectorSubsystem>() : nullptr;
	if (!Director)
	{
		return EUmbrellaShotResult::Ignored;
	}
	const EKeeperHitOutcome Outcome = Director->HandlePlayerShot(PartId, Shot.Damage);
	return Outcome == EKeeperHitOutcome::PassThrough ? EUmbrellaShotResult::Ignored : EUmbrellaShotResult::Consumed;
}

#pragma once

#include "CoreMinimal.h"
#include "Components/BoxComponent.h"
#include "Encounter/KeeperFightModel.h"
#include "Projectile/UmbrellaShotReceiver.h"
#include "KeeperPartComponent.generated.h"

/** One hittable region of the Keeper (wings, clock, eye, a mechanism or its moving head). Forwards player shots to the director. */
UCLASS(ClassGroup = (UmbrellaElla))
class UMBRELLAELLA_API UKeeperPartComponent : public UBoxComponent, public IUmbrellaShotReceiver
{
	GENERATED_BODY()

public:
	UKeeperPartComponent();

	void Configure(EKeeperPart InPart, const FVector2D& HalfExtent);

	EKeeperPart GetPart() const { return PartId; }

	/** Collision on = player shots can touch it; off = shots pass through (broken, away or not shown). */
	void SetHittable(bool bHittable);

	virtual EUmbrellaShotResult ReceiveShot(const FUmbrellaShotSpec& Shot, const FVector& HitLocation) override;

private:
	EKeeperPart PartId = EKeeperPart::Count;
};

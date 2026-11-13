#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "UmbrellaHitProtectionSource.generated.h"

UINTERFACE(MinimalAPI)
class UUmbrellaHitProtectionSource : public UInterface
{
	GENERATED_BODY()
};

/**
 * A component on Ella that can protect her from ordinary hits for a moment (the overhead hop). Health asks every
 * component of its owner that implements this before a hit lands; it never needs to know which module answers.
 * This protection is separate from Health's own post-hit window: a hit it blocks starts no post-hit window.
 */
class UMBRELLAELLA_API IUmbrellaHitProtectionSource
{
	GENERATED_BODY()

public:
	/** True while ordinary hits must not land. Sources that bypass protection (hostile gusts) ignore it. */
	virtual bool IsProtectingFromHits() const = 0;
};

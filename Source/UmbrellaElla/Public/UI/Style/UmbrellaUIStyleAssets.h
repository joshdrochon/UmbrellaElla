#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "UmbrellaUIStyleAssets.generated.h"

class UFont;
class UFontFace;
class UTexture2D;
struct FUmbrellaUIStyleData;

/**
 * Holds what the shared UI style paints with: the textures (referenced by a native class, so they are cooked), the
 * font objects built from the embedded bytes (so they are never garbage collected) and the brushes made from them.
 * Only FUmbrellaUIStyle reads it.
 */
UCLASS()
class UMBRELLAELLA_API UUmbrellaUIStyleAssets : public UObject
{
	GENERATED_BODY()

public:
	UUmbrellaUIStyleAssets();

	/** The painted paper ground every menu sits on (Art/Source/UI/Ground/build_ground.py). Null when not imported. */
	UTexture2D* GetGround() const { return Ground; }

	/** The etched HUD clock face. Null when not imported. */
	UTexture2D* GetClockFace() const { return ClockFace; }

	/** The painted title lockup (Art/Source/UI/Lockup/build_lockup.py), transparent. Null when not imported. */
	UTexture2D* GetTitleLockup() const { return TitleLockup; }

	UFontFace* GetDisplayFace() const { return DisplayFace; }
	UFont* GetDisplayCanvasFont() const { return DisplayCanvasFont; }
	void SetDisplayFonts(UFontFace* InFace, UFont* InCanvasFont);

	/** Brushes and widget styles, built at first use and kept for the life of the module. */
	const TSharedPtr<FUmbrellaUIStyleData>& GetStyleData() const { return StyleData; }
	void SetStyleData(const TSharedPtr<FUmbrellaUIStyleData>& InData) { StyleData = InData; }

private:
	UPROPERTY()
	TObjectPtr<UTexture2D> Ground;

	UPROPERTY()
	TObjectPtr<UTexture2D> ClockFace;

	UPROPERTY()
	TObjectPtr<UTexture2D> TitleLockup;

	/** The display face, made at first use from the bytes in UmbrellaStorybookFont.inl. */
	UPROPERTY(Transient)
	TObjectPtr<UFontFace> DisplayFace;

	/** The same face wrapped for the HUD canvas. */
	UPROPERTY(Transient)
	TObjectPtr<UFont> DisplayCanvasFont;

	TSharedPtr<FUmbrellaUIStyleData> StyleData;
};

#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Components/StaticMeshComponent.h"
#include "Core/EllaCharacter.h"
#include "Engine/Texture2D.h"
#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "Feedback/Art/ArtSlot.h"
#include "Materials/MaterialInterface.h"
#include "Tests/Shared/UmbrellaTestWorld.h"

/**
 * Josh, 13 Nov: "when Ella gets hit she turns into a black box for a moment". T_Ella_Hurt_PH is a 23688 x 565 strip,
 * over the 16384 px texture limit, and drew as a solid black box. An oversized picture is never handed out to draw.
 */
namespace
{
	/** Metal's 2D texture edge limit, written out here so the check does not lean on ArtSlot::CanGpuDraw itself. */
	constexpr int32 GpuEdgeLimit = 16384;

	bool UnderGpuLimit(const FIntPoint& Size)
	{
		return Size.X >= 1 && Size.Y >= 1 && Size.X <= GpuEdgeLimit && Size.Y <= GpuEdgeLimit;
	}

	constexpr EAutomationTestFlags HurtTestFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter;

	UTexture* DrawnPicture(const UStaticMeshComponent* Mesh)
	{
		const UMaterialInterface* Material = IsValid(Mesh) && Mesh->GetNumMaterials() > 0 ? Mesh->GetMaterial(0) : nullptr;
		UTexture* Picture = nullptr;
		if (Material)
		{
			Material->GetTextureParameterValue(FHashedMaterialParameterInfo(FName(TEXT("Art"))), Picture);
		}
		return Picture;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FArtSlotCanGpuDraw, "UmbrellaElla.Feedback.ArtSlot.CanGpuDraw", HurtTestFlags)

bool FArtSlotCanGpuDraw::RunTest(const FString& Parameters)
{
	TestFalse(TEXT("the old hurt strip (23688 x 565) does not fit"), ArtSlot::CanGpuDraw(23688, 565));
	TestTrue(TEXT("16384 x 16384 fits"), ArtSlot::CanGpuDraw(16384, 16384));
	TestFalse(TEXT("16385 tall does not fit"), ArtSlot::CanGpuDraw(100, 16385));
	TestFalse(TEXT("an empty picture does not fit"), ArtSlot::CanGpuDraw(0, 10));
	// Every catalogue picture the game can load is one the GPU can draw.
	for (const FArtSlotRow& Row : ArtSlot::Rows())
	{
		if (const UTexture2D* Texture = ArtSlot::LoadTexture(Row))
		{
			const FIntPoint Size = ArtSlot::PictureSize(Texture);
			TestTrue(FString::Printf(TEXT("%s (%s) %d x %d fits"), Row.Visual, *Texture->GetName(), Size.X, Size.Y), UnderGpuLimit(Size));
			// UE 5.8.4 Engine/Classes/Engine/Texture.h: UTexture::VirtualTextureStreaming (line 1611). The unlit art-slot
			// material samples a plain texture; a virtual one drew T_Ella_Hurt_PH as a solid black box.
			TestFalse(FString::Printf(TEXT("%s (%s) is not a virtual texture"), Row.Visual, *Texture->GetName()), Texture->VirtualTextureStreaming != 0);
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEllaHurtNeverBlack, "UmbrellaElla.Feedback.World.EllaHurtNeverBlack", HurtTestFlags)

bool FEllaHurtNeverBlack::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	UEllaAnimPresenterComponent* Look = Ella ? Ella->GetAnimPresenter() : nullptr;
	const UStaticMeshComponent* Mesh = Ella ? FindObjectFast<UStaticMeshComponent>(Ella, FName(TEXT("EllaStandIn"))) : nullptr;
	if (!TestNotNull(TEXT("ella"), Ella) || !TestNotNull(TEXT("presenter"), Look) || !TestNotNull(TEXT("Ella's picture"), Mesh))
	{
		return false;
	}
	for (const EEllaVisualState State : { EEllaVisualState::Hurt, EEllaVisualState::Idle, EEllaVisualState::Down, EEllaVisualState::Shoot, EEllaVisualState::Absorb })
	{
		Look->SetVisualState(State);
		const UTexture2D* Picture = Cast<UTexture2D>(DrawnPicture(Mesh));
		const FString Name = StaticEnum<EEllaVisualState>()->GetNameStringByValue(static_cast<int64>(State));
		if (!TestNotNull(FString::Printf(TEXT("%s: Ella draws a picture"), *Name), Picture) || !TestTrue(FString::Printf(TEXT("%s: art on"), *Name), ArtSlot::HasArt(Mesh)))
		{
			continue;
		}
		const FIntPoint Size = ArtSlot::PictureSize(Picture);
		AddInfo(FString::Printf(TEXT("%s draws %s, %d x %d"), *Name, *Picture->GetName(), Size.X, Size.Y));
		TestFalse(FString::Printf(TEXT("%s: %s is not a virtual texture (else a black box)"), *Name, *Picture->GetName()), Picture->VirtualTextureStreaming != 0);
		TestTrue(FString::Printf(TEXT("%s: %s %d x %d is within the %d px limit (else a black box)"), *Name, *Picture->GetName(), Size.X, Size.Y,
			GpuEdgeLimit), UnderGpuLimit(Size));
	}
	return true;
}

#endif

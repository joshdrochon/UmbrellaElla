#include "Attack/AimedBeamActor.h"
#include "Attack/AttackTuning.h"
#include "Attack/StreamBeamActor.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Feedback/Art/ArtSlot.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Owl/KeeperLook.h"
#include "Projectile/UmbrellaShotSpec.h"
#include "UObject/StrongObjectPtr.h"

namespace
{
	/** Ricky's Other Realm study light: warm ivory (the art bible outline #FFE6C4), brass, ash. */
	const FLinearColor RibbonCore = FLinearColor(FColor(0xFF, 0xEE, 0xD2));
	const FLinearColor RibbonBrass = FLinearColor(FColor(0xD9, 0xA8, 0x5C));
	const FLinearColor RibbonAsh = FLinearColor(FColor(0x8A, 0x7A, 0x6A));

	/** Smooth value noise in 0..1 from an integer lattice (deterministic, no engine random state). */
	float RibbonHash(int32 X, int32 Seed)
	{
		uint32 H = static_cast<uint32>(X) * 374761393u + static_cast<uint32>(Seed) * 668265263u;
		H = (H ^ (H >> 13)) * 1274126177u;
		return static_cast<float>((H ^ (H >> 16)) & 0xFFFF) / 65535.0f;
	}

	float RibbonNoise(float X, int32 Seed)
	{
		const int32 I = FMath::FloorToInt(X);
		const float F = X - static_cast<float>(I);
		const float S = F * F * (3.0f - 2.0f * F);
		return FMath::Lerp(RibbonHash(I, Seed), RibbonHash(I + 1, Seed), S);
	}

	TStrongObjectPtr<UTexture2D>& RibbonCache()
	{
		static TStrongObjectPtr<UTexture2D> Cache;
		return Cache;
	}
}

AAimedBeamActor::AAimedBeamActor()
{
	PrimaryActorTick.bCanEverTick = false;
	Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
	Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Visual->SetGenerateOverlapEvents(false);
	Visual->SetCastShadow(false);
	SetRootComponent(Visual);
}

FColor AAimedBeamActor::RibbonTexel(int32 X, int32 Y)
{
	const float U = (static_cast<float>(X) + 0.5f) / RibbonWidth;
	const float V = (static_cast<float>(Y) + 0.5f) / RibbonHeight;
	// Ragged soft edge: the half-thickness wanders a little along the beam, like a dry brush.
	const float Edge = 0.86f + 0.14f * RibbonNoise(U * 18.0f, 7) - 0.06f * RibbonNoise(U * 61.0f, 11);
	const float Across = FMath::Abs(V - 0.5f) * 2.0f / FMath::Max(0.2f, Edge);
	const float Alpha = FMath::Clamp(1.0f - FMath::SmoothStep(0.35f, 1.0f, Across), 0.0f, 1.0f);
	// Colour: ivory core -> brass -> ash toward the edge.
	FLinearColor Colour = Across < 0.45f ? FMath::Lerp(RibbonCore, RibbonBrass, Across / 0.45f)
		: FMath::Lerp(RibbonBrass, RibbonAsh, FMath::Clamp((Across - 0.45f) / 0.55f, 0.0f, 1.0f));
	// Painted streaks: each row gets its own slow grain along the beam (+-12%), plus a fine stroke texture.
	const int32 Row = Y / 3;
	const float Grain = 0.88f + 0.24f * RibbonNoise(U * 9.0f + static_cast<float>(Row) * 3.1f, 23 + Row)
		- 0.08f * RibbonNoise(U * 140.0f, 31 + Row);
	Colour *= Grain;
	Colour.A = Alpha;
	return Colour.GetClamped().ToFColor(true);
}

UTexture2D* AAimedBeamActor::RibbonTexture()
{
	if (RibbonCache().IsValid())
	{
		return RibbonCache().Get();
	}
	UTexture2D* Texture = UTexture2D::CreateTransient(RibbonWidth, RibbonHeight, PF_B8G8R8A8, TEXT("T_AimedBeamRibbon"));
	if (!Texture)
	{
		return nullptr;
	}
	Texture->SRGB = true;
	Texture->Filter = TF_Bilinear;
	Texture->AddressX = TA_Clamp;
	Texture->AddressY = TA_Clamp;
	FTexture2DMipMap& Mip = Texture->GetPlatformData()->Mips[0];
	FColor* Texels = static_cast<FColor*>(Mip.BulkData.Lock(LOCK_READ_WRITE));
	for (int32 Y = 0; Y < RibbonHeight; ++Y)
	{
		for (int32 X = 0; X < RibbonWidth; ++X)
		{
			Texels[Y * RibbonWidth + X] = RibbonTexel(X, Y);
		}
	}
	Mip.BulkData.Unlock();
	Texture->UpdateResource();
	RibbonCache().Reset(Texture);
	return Texture;
}

void AAimedBeamActor::HitDepth(float& OutCenterY, float& OutHalfDepth)
{
	const float MinY = UmbrellaDrawOrder::KeeperY - KeeperLook::PartDepth;
	const float MaxY = UmbrellaDrawOrder::ProjectileY + GetDefault<UUmbrellaTuning>()->Attack.StreamDepthHalfExtent;
	OutCenterY = 0.5f * (MinY + MaxY);
	OutHalfDepth = 0.5f * (MaxY - MinY);
}

void AAimedBeamActor::Place(const FVector& Muzzle, float Length, float Width)
{
	BeamMuzzle = Muzzle;
	BeamMuzzle.Y = UmbrellaDrawOrder::ProjectileY;
	BeamWidth = FMath::Max(Width, 1.0f);
	float CenterY = 0.0f;
	float HalfDepth = 0.0f;
	HitDepth(CenterY, HalfDepth);
	EffectiveLength = AStreamBeamActor::ClipToBlockers(GetWorld(), this, FVector(BeamMuzzle.X, CenterY, BeamMuzzle.Z), FMath::Max(Length, 0.0f), BeamWidth, HalfDepth);
	DrawRibbon(1.0f);
}

int32 AAimedBeamActor::Fire(const FUmbrellaShotSpec& Shot)
{
	float CenterY = 0.0f;
	float HalfDepth = 0.0f;
	HitDepth(CenterY, HalfDepth);
	return AStreamBeamActor::HitBox(GetWorld(), this, FVector(BeamMuzzle.X, CenterY, BeamMuzzle.Z), EffectiveLength, BeamWidth, HalfDepth, Shot);
}

void AAimedBeamActor::Follow(const FVector& Muzzle, float Age01)
{
	BeamMuzzle.X = Muzzle.X;
	BeamMuzzle.Z = Muzzle.Z;
	// Full width for most of its life, then it thins to a hairline (looks only; damage already landed).
	const float Age = FMath::Clamp(Age01, 0.0f, 1.0f);
	DrawRibbon(Age < FullWidthShare ? 1.0f : FMath::Lerp(1.0f, 0.15f, FMath::SmoothStep(FullWidthShare, 1.0f, Age)));
}

void AAimedBeamActor::DrawRibbon(float Thickness)
{
	if (!Visual->GetStaticMesh())
	{
		UStaticMesh* Plane = LoadObject<UStaticMesh>(nullptr, UmbrellaArtSlotConst::PlanePath, nullptr, LOAD_NoWarn | LOAD_Quiet);
		Ribbon = RibbonTexture();
		UMaterialInterface* Fade = LoadObject<UMaterialInterface>(nullptr, UmbrellaArtSlotConst::EdgeFadeMaterialPath, nullptr, LOAD_NoWarn | LOAD_Quiet);
		UMaterialInterface* Base = Fade ? Fade : LoadObject<UMaterialInterface>(nullptr, UmbrellaArtSlotConst::MaterialPath, nullptr, LOAD_NoWarn | LOAD_Quiet);
		if (!Plane || !Base || !Ribbon)
		{
			return;
		}
		Visual->SetStaticMesh(Plane);
		UMaterialInstanceDynamic* Dynamic = UMaterialInstanceDynamic::Create(Base, this);
		Dynamic->SetTextureParameterValue(TEXT("Art"), Ribbon);
		Dynamic->SetScalarParameterValue(TEXT("Cols"), 1.0f);
		Dynamic->SetScalarParameterValue(TEXT("Frame"), 0.0f);
		Dynamic->SetScalarParameterValue(TEXT("TileU"), 1.0f);
		Dynamic->SetScalarParameterValue(TEXT("TileV"), 1.0f);
		Dynamic->SetVectorParameterValue(TEXT("Tint"), FLinearColor::White);
		Dynamic->SetScalarParameterValue(TEXT("FadeLeft"), NearFade);
		Dynamic->SetScalarParameterValue(TEXT("FadeRight"), FarFade);
		Visual->SetMaterial(0, Dynamic);
		// Plane X stays world X (screen right); the normal turns to +Y, toward the camera (as ArtSlot::Apply).
		Visual->SetWorldRotation(FRotationMatrix::MakeFromXZ(FVector::XAxisVector, FVector::YAxisVector).Rotator());
	}
	SetActorLocation(BeamMuzzle + FVector(EffectiveLength * 0.5f, 0.0f, 0.0f));
	const float Edge = UmbrellaArtSlotConst::PlaneEdge;
	Visual->SetWorldScale3D(FVector(FMath::Max(EffectiveLength, 0.01f) / Edge, FMath::Max(BeamWidth * VisualWidthScale * Thickness, 0.01f) / Edge, 1.0f));
	Visual->SetVisibility(EffectiveLength > 0.0f);
}

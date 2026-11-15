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
#include "Misc/Crc.h"
#include "Owl/KeeperLook.h"
#include "Projectile/UmbrellaShotSpec.h"

namespace
{
	/** Smooth value noise in 0..1 from an integer lattice (deterministic, no engine random state). */
	float RibbonHash(int32 X, int32 Seed)
	{
		return static_cast<float>(FCrc::MemCrc32(&X, sizeof(X), static_cast<uint32>(Seed))) / static_cast<float>(MAX_uint32);
	}

	float RibbonNoise(float X, int32 Seed)
	{
		const int32 I = FMath::FloorToInt(X);
		const float F = X - static_cast<float>(I);
		return FMath::Lerp(RibbonHash(I, Seed), RibbonHash(I + 1, Seed), FMath::SmoothStep(0.0f, 1.0f, F));
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
	const float Edge = AimedRibbonLook::EdgeBase + AimedRibbonLook::EdgeWander * RibbonNoise(U * AimedRibbonLook::EdgeWanderFreq, AimedRibbonLook::EdgeWanderSeed) - AimedRibbonLook::EdgeBite * RibbonNoise(U * AimedRibbonLook::EdgeBiteFreq, AimedRibbonLook::EdgeBiteSeed);
	const float Across = FMath::Abs(V - 0.5f) * 2.0f / FMath::Max(AimedRibbonLook::EdgeMin, Edge);
	const float Alpha = FMath::Clamp(1.0f - FMath::SmoothStep(AimedRibbonLook::AlphaSoftFrom, 1.0f, Across), 0.0f, 1.0f);
	// Colour: ivory core -> brass -> ash toward the edge.
	FLinearColor Colour = Across < AimedRibbonLook::CoreShare ? FMath::Lerp(AimedRibbonLook::Core, AimedRibbonLook::Brass, Across / AimedRibbonLook::CoreShare)
		: FMath::Lerp(AimedRibbonLook::Brass, AimedRibbonLook::Ash, FMath::Clamp((Across - AimedRibbonLook::CoreShare) / (1.0f - AimedRibbonLook::CoreShare), 0.0f, 1.0f));
	// Painted streaks: each band of rows gets its own slow grain along the beam, plus a fine stroke texture.
	const int32 Row = Y / AimedRibbonLook::StreakRows;
	const float Grain = AimedRibbonLook::GrainBase + AimedRibbonLook::GrainAmount * RibbonNoise(U * AimedRibbonLook::GrainFreq + static_cast<float>(Row) * AimedRibbonLook::GrainRowPhase, AimedRibbonLook::GrainSeed + Row)
		- AimedRibbonLook::StrokeAmount * RibbonNoise(U * AimedRibbonLook::StrokeFreq, AimedRibbonLook::StrokeSeed + Row);
	Colour *= Grain;
	Colour.A = Alpha;
	return Colour.GetClamped().ToFColor(true);
}

UTexture2D* AAimedBeamActor::MakeRibbonTexture(UObject* Outer)
{
	UTexture2D* Texture = UTexture2D::CreateTransient(RibbonWidth, RibbonHeight, PF_B8G8R8A8, NAME_None);
	if (!Texture)
	{
		return nullptr;
	}
	if (Outer)
	{
		Texture->Rename(nullptr, Outer, REN_DontCreateRedirectors | REN_NonTransactional);
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
	DrawRibbon(Age < FullWidthShare ? 1.0f : FMath::Lerp(1.0f, AimedRibbonLook::EndThickness, FMath::SmoothStep(FullWidthShare, 1.0f, Age)));
}

void AAimedBeamActor::DrawRibbon(float Thickness)
{
	if (!Visual->GetStaticMesh())
	{
		UStaticMesh* Plane = LoadObject<UStaticMesh>(nullptr, UmbrellaArtSlotConst::PlanePath, nullptr, LOAD_NoWarn | LOAD_Quiet);
		Ribbon = MakeRibbonTexture(this);
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
	Visual->SetWorldScale3D(FVector(FMath::Max(EffectiveLength, AimedRibbonLook::MinDrawSize) / Edge, FMath::Max(BeamWidth * VisualWidthScale * Thickness, AimedRibbonLook::MinDrawSize) / Edge, 1.0f));
	Visual->SetVisibility(EffectiveLength > 0.0f);
}

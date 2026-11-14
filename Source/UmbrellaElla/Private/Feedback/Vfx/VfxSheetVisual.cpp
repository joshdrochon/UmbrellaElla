#include "Feedback/Vfx/VfxSheetVisual.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Feedback/Vfx/VfxCatalog.h"
#include "Feedback/Vfx/VfxLightPolicy.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

namespace
{
	const FName VfxArtTag(TEXT("VfxArt"));
	const FName VfxSheetParam(TEXT("Sheet"));
	const FName VfxColsParam(TEXT("Cols"));
	const FName VfxFrameParam(TEXT("Frame"));
	const FName VfxOpacityParam(TEXT("Opacity"));
	const FName VfxTintParam(TEXT("Tint"));
	// Slots vfx-material:M_VFX_Sheet and M_VFX_Spill: the real material first, the tracked _PH one as fallback.
	const TCHAR* const VfxSheetMaterialPaths[] = { TEXT("/Game/UmbrellaElla/Art/VFX/M_VFX_Sheet.M_VFX_Sheet"), TEXT("/Game/UmbrellaElla/Art/VFX/M_VFX_Sheet_PH.M_VFX_Sheet_PH") };
	const TCHAR* const VfxSpillMaterialPaths[] = { TEXT("/Game/UmbrellaElla/Art/VFX/M_VFX_Spill.M_VFX_Spill"), TEXT("/Game/UmbrellaElla/Art/VFX/M_VFX_Spill_PH.M_VFX_Spill_PH") };
	const TCHAR* const VfxPlanePath = TEXT("/Engine/BasicShapes/Plane.Plane");
	const TCHAR* const VfxSpherePath = TEXT("/Engine/BasicShapes/Sphere.Sphere");

	UMaterialInterface* LoadVfxMaterial(const TCHAR* const (&Paths)[2])
	{
		for (const TCHAR* Path : Paths)
		{
			if (UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, Path, nullptr, LOAD_NoWarn | LOAD_Quiet))
			{
				return Material;
			}
		}
		return nullptr;
	}

	UTexture2D* LoadVfxSheet(const FVfxArtRow& Row)
	{
		for (const FString& Path : VfxCatalog::TexturePaths(Row))
		{
			if (UTexture2D* Sheet = LoadObject<UTexture2D>(nullptr, *Path, nullptr, LOAD_NoWarn | LOAD_Quiet))
			{
				return Sheet;
			}
		}
		return nullptr;
	}

	void DisableVfxCollision(UStaticMeshComponent* Mesh)
	{
		Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Mesh->SetGenerateOverlapEvents(false);
		Mesh->SetCastShadow(false);
	}
}

FRotator VfxSheetVisual::FacingCamera()
{
	// Plane X stays world X (screen right); the plane's normal turns to +Y, toward the camera.
	return FRotationMatrix::MakeFromXZ(FVector::XAxisVector, FVector::YAxisVector).Rotator();
}

FRotator VfxSheetVisual::FacingCameraToward(float TravelX)
{
	// Plane X along the travel; the normal stays +Y (toward the camera), so the quad turns in the screen plane only.
	const FVector Along = TravelX < 0.0f ? -FVector::XAxisVector : FVector::XAxisVector;
	return FRotationMatrix::MakeFromXZ(Along, FVector::YAxisVector).Rotator();
}

UStaticMeshComponent* VfxSheetVisual::Build(AActor* Owner, const FVfxArtRow& Row, const FVector2D& Size)
{
	if (!IsValid(Owner))
	{
		return nullptr;
	}
	UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(Owner, TEXT("VfxVisual"));
	DisableVfxCollision(Mesh);
	UTexture2D* Sheet = LoadVfxSheet(Row);
	UMaterialInterface* Material = Sheet ? LoadVfxMaterial(VfxSheetMaterialPaths) : nullptr;
	UStaticMesh* Plane = Material ? LoadObject<UStaticMesh>(nullptr, VfxPlanePath) : nullptr;
	if (Plane)
	{
		Mesh->SetStaticMesh(Plane);
		UMaterialInstanceDynamic* Dynamic = UMaterialInstanceDynamic::Create(Material, Mesh);
		Dynamic->SetTextureParameterValue(VfxSheetParam, Sheet);
		Dynamic->SetScalarParameterValue(VfxColsParam, static_cast<float>(Row.Frames));
		Dynamic->SetScalarParameterValue(VfxFrameParam, 0.0f);
		Dynamic->SetScalarParameterValue(VfxOpacityParam, 1.0f);
		Mesh->SetMaterial(0, Dynamic);
		Mesh->ComponentTags.Add(VfxArtTag);
		Mesh->SetRelativeRotation(FacingCamera());
	}
	else if (UStaticMesh* Sphere = LoadObject<UStaticMesh>(nullptr, VfxSpherePath))
	{
		Mesh->SetStaticMesh(Sphere);
		if (!VfxCatalog::IsStandInAdmitted(Row))
		{
			// visualqa: the sheet's stand-in was refused (framed or unkeyed); a grey sphere is no better. Draw nothing.
			Mesh->SetRenderInMainPass(false);
			Mesh->SetRenderInDepthPass(false);
		}
	}
	Owner->SetRootComponent(Mesh);
	Mesh->RegisterComponent();
	Resize(Mesh, Size);
	return Mesh;
}

void VfxSheetVisual::Resize(UStaticMeshComponent* Visual, const FVector2D& Size)
{
	if (!IsValid(Visual))
	{
		return;
	}
	if (HasArt(Visual))
	{
		// The plane lies in its local X/Y; local Y is the sheet's height.
		Visual->SetRelativeScale3D(FVector(Size.X / ShapeEdge, Size.Y / ShapeEdge, 1.0));
	}
	else
	{
		Visual->SetRelativeScale3D(FVector(Size.X, FMath::Min(Size.X, Size.Y), Size.Y) * (StandInFraction / ShapeEdge));
	}
}

bool VfxSheetVisual::HasArt(const UStaticMeshComponent* Visual)
{
	return IsValid(Visual) && Visual->ComponentHasTag(VfxArtTag);
}

void VfxSheetVisual::SetFrame(UStaticMeshComponent* Visual, int32 Frame)
{
	if (UMaterialInstanceDynamic* Dynamic = IsValid(Visual) ? Cast<UMaterialInstanceDynamic>(Visual->GetMaterial(0)) : nullptr)
	{
		Dynamic->SetScalarParameterValue(VfxFrameParam, static_cast<float>(Frame));
	}
}

void VfxSheetVisual::SetOpacity(UStaticMeshComponent* Visual, float Opacity)
{
	if (UMaterialInstanceDynamic* Dynamic = IsValid(Visual) ? Cast<UMaterialInstanceDynamic>(Visual->GetMaterial(0)) : nullptr)
	{
		Dynamic->SetScalarParameterValue(VfxOpacityParam, Opacity);
	}
}

UPointLightComponent* VfxSheetVisual::AddLight(AActor* Owner, const FVfxLightPlan& Plan)
{
	if (!IsValid(Owner) || !Plan.bPointLight)
	{
		return nullptr;
	}
	UPointLightComponent* Light = NewObject<UPointLightComponent>(Owner, TEXT("VfxLight"));
	Light->SetIntensity(Plan.Intensity);
	Light->SetAttenuationRadius(Plan.Radius);
	Light->SetLightColor(Plan.Colour);
	Light->SetCastShadows(false);
	Light->SetupAttachment(Owner->GetRootComponent());
	Light->RegisterComponent();
	return Light;
}

UStaticMeshComponent* VfxSheetVisual::AddSpill(AActor* Owner, const FVfxLightPlan& Plan)
{
	if (!IsValid(Owner) || !Plan.bSpillOverlay)
	{
		return nullptr;
	}
	UMaterialInterface* Material = LoadVfxMaterial(VfxSpillMaterialPaths);
	UStaticMesh* Plane = Material ? LoadObject<UStaticMesh>(nullptr, VfxPlanePath) : nullptr;
	if (!Plane)
	{
		return nullptr;
	}
	UStaticMeshComponent* Spill = NewObject<UStaticMeshComponent>(Owner, TEXT("VfxSpill"));
	DisableVfxCollision(Spill);
	Spill->SetStaticMesh(Plane);
	UMaterialInstanceDynamic* Dynamic = UMaterialInstanceDynamic::Create(Material, Spill);
	Dynamic->SetVectorParameterValue(VfxTintParam, Plan.Colour);
	Dynamic->SetScalarParameterValue(VfxOpacityParam, Plan.SpillOpacity);
	Spill->SetMaterial(0, Dynamic);
	Spill->SetUsingAbsoluteLocation(true);
	Spill->SetUsingAbsoluteRotation(true);
	Spill->SetUsingAbsoluteScale(true);
	Spill->SetupAttachment(Owner->GetRootComponent());
	Spill->RegisterComponent();
	Spill->SetWorldRotation(FacingCamera());
	Spill->SetWorldScale3D(FVector(Plan.SpillSize / ShapeEdge, Plan.SpillSize / ShapeEdge, 1.0));
	const FVector At = Owner->GetActorLocation();
	Spill->SetWorldLocation(FVector(At.X, VfxLightPolicy::SpillLayerY(), At.Z));
	return Spill;
}

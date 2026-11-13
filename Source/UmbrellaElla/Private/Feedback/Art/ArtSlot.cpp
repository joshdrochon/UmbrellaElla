#include "Feedback/Art/ArtSlot.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Materials/Material.h"

namespace
{
	const FName ArtSlotTag(TEXT("ArtSlotArt"));
	const FName ArtSlotParam(TEXT("Art"));
	const FName ArtSlotColsParam(TEXT("Cols"));
	const FName ArtSlotFrameParam(TEXT("Frame"));
	const FName ArtSlotTintParam(TEXT("Tint"));
	const FName ArtSlotTileUParam(TEXT("TileU"));
	const FName ArtSlotTileVParam(TEXT("TileV"));

	const FArtSlotRow ArtSlotRows[] = {
#include "Feedback/Art/ArtSlotCatalog.inc"
	};
}

TConstArrayView<FArtSlotRow> ArtSlot::Rows()
{
	return MakeArrayView(ArtSlotRows);
}

const FArtSlotRow* ArtSlot::Find(const TCHAR* Visual)
{
	for (const FArtSlotRow& Row : ArtSlotRows)
	{
		if (FCString::Strcmp(Row.Visual, Visual) == 0)
		{
			return &Row;
		}
	}
	return nullptr;
}

FString ArtSlot::SlotPath(const FArtSlotRow& Row)
{
	return FString::Printf(TEXT("%s/%s/%s"), UmbrellaArtSlotConst::GameRoot, Row.Folder, Row.Asset);
}

TArray<FString> ArtSlot::TexturePaths(const FArtSlotRow& Row)
{
	const FString Passed = SlotPath(Row);
	const FString Placeholder = Passed + UmbrellaArtSlotConst::PlaceholderSuffix;
	return { Passed + TEXT(".") + Row.Asset, Placeholder + TEXT(".") + Row.Asset + UmbrellaArtSlotConst::PlaceholderSuffix };
}

UTexture2D* ArtSlot::LoadTexture(const FArtSlotRow& Row)
{
	for (const FString& Path : TexturePaths(Row))
	{
		if (UTexture2D* Texture = LoadObject<UTexture2D>(nullptr, *Path, nullptr, LOAD_NoWarn | LOAD_Quiet))
		{
			return Texture;
		}
	}
	return nullptr;
}

FVector ArtSlot::PlaneScaleFor(const FVector& BoxScale)
{
	// The plane lies in its local X/Y, and its local Y runs down the picture; the stand-in's height is Z.
	return FVector(BoxScale.X, BoxScale.Z, 1.0);
}

EArtSlotDraw ArtSlot::Apply(UStaticMeshComponent* Mesh, UTexture2D* Texture, const FArtSlotRow& Row, const FVector& BoxScale)
{
	if (!IsValid(Mesh) || !IsValid(Texture))
	{
		return EArtSlotDraw::NoTexture;
	}
	UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, UmbrellaArtSlotConst::MaterialPath, nullptr, LOAD_NoWarn | LOAD_Quiet);
	UStaticMesh* Plane = Material ? LoadObject<UStaticMesh>(nullptr, UmbrellaArtSlotConst::PlanePath, nullptr, LOAD_NoWarn | LOAD_Quiet) : nullptr;
	if (!Plane)
	{
		return EArtSlotDraw::NoMaterial;
	}
	Mesh->SetStaticMesh(Plane);
	UMaterialInstanceDynamic* Dynamic = UMaterialInstanceDynamic::Create(Material, Mesh);
	Dynamic->SetTextureParameterValue(ArtSlotParam, Texture);
	Dynamic->SetScalarParameterValue(ArtSlotColsParam, static_cast<float>(FMath::Max(1, Row.Cols)));
	Dynamic->SetScalarParameterValue(ArtSlotFrameParam, 0.0f);
	const FVector Plane3 = PlaneScaleFor(BoxScale);
	const float RepeatsU = Row.bTile ? FMath::Max(1.0f, static_cast<float>(Plane3.X) * UmbrellaArtSlotConst::PlaneEdge / UmbrellaArtSlotConst::TileWorldSize) : 1.0f;
	const float RepeatsV = Row.bTile ? FMath::Max(1.0f, static_cast<float>(Plane3.Y) * UmbrellaArtSlotConst::PlaneEdge / UmbrellaArtSlotConst::TileWorldSize) : 1.0f;
	Dynamic->SetScalarParameterValue(ArtSlotTileUParam, RepeatsU);
	Dynamic->SetScalarParameterValue(ArtSlotTileVParam, RepeatsV);
	Mesh->SetMaterial(0, Dynamic);
	Mesh->ComponentTags.AddUnique(ArtSlotTag);
	// Plane X stays world X (screen right); the plane's normal turns to +Y, toward the camera.
	Mesh->SetRelativeRotation(FRotationMatrix::MakeFromXZ(FVector::XAxisVector, FVector::YAxisVector).Rotator());
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetGenerateOverlapEvents(false);
	Mesh->SetCastShadow(false);
	Mesh->SetRelativeScale3D(Plane3);
	return EArtSlotDraw::Drawn;
}

void ArtSlot::SetFlatUnlit(UStaticMeshComponent* Mesh, UObject* Outer, const FLinearColor& Color)
{
	if (!IsValid(Mesh))
	{
		return;
	}
	UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, UmbrellaArtSlotConst::MaterialPath, nullptr, LOAD_NoWarn | LOAD_Quiet);
	UTexture2D* White = LoadObject<UTexture2D>(nullptr, UmbrellaArtSlotConst::WhiteTexturePath, nullptr, LOAD_NoWarn | LOAD_Quiet);
	if (!Material || !White)
	{
		return;
	}
	UMaterialInstanceDynamic* Dynamic = UMaterialInstanceDynamic::Create(Material, IsValid(Outer) ? Outer : Mesh);
	Dynamic->SetTextureParameterValue(ArtSlotParam, White);
	Dynamic->SetVectorParameterValue(ArtSlotTintParam, Color);
	Mesh->SetMaterial(0, Dynamic);
	Mesh->SetCastShadow(false);
}

bool ArtSlot::IsUnlit(const UStaticMeshComponent* Mesh)
{
	const UMaterialInterface* Material = IsValid(Mesh) ? Mesh->GetMaterial(0) : nullptr;
	const UMaterial* Base = Material ? Material->GetMaterial() : nullptr;
	return Base && Base->GetShadingModels().HasOnlyShadingModel(MSM_Unlit);
}

EArtSlotDraw ArtSlot::ApplyRow(UStaticMeshComponent* Mesh, const FArtSlotRow& Row, const FVector& BoxScale)
{
	return Apply(Mesh, LoadTexture(Row), Row, BoxScale);
}

void ArtSlot::SetTexture(UStaticMeshComponent* Mesh, UTexture2D* Texture)
{
	if (UMaterialInstanceDynamic* Dynamic = IsValid(Mesh) && IsValid(Texture) ? Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(0)) : nullptr)
	{
		Dynamic->SetTextureParameterValue(ArtSlotParam, Texture);
	}
}

bool ArtSlot::HasArt(const UStaticMeshComponent* Mesh)
{
	return IsValid(Mesh) && Mesh->ComponentHasTag(ArtSlotTag);
}

void ArtSlot::SetWorldBoxScale(UStaticMeshComponent* Mesh, const FVector& BoxScale)
{
	if (IsValid(Mesh))
	{
		Mesh->SetWorldScale3D(HasArt(Mesh) ? PlaneScaleFor(BoxScale) : BoxScale);
	}
}

void ArtSlot::SetBoxScale(UStaticMeshComponent* Mesh, const FVector& BoxScale)
{
	if (IsValid(Mesh))
	{
		Mesh->SetRelativeScale3D(HasArt(Mesh) ? PlaneScaleFor(BoxScale) : BoxScale);
	}
}

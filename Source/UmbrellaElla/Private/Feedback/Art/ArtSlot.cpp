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

	// Loader cache: engine assets and textures are looked up once. Weak pointers, so a garbage-collected or reimported asset reloads.
	TWeakObjectPtr<UMaterialInterface> ArtSlotCachedMaterial;
	TWeakObjectPtr<UStaticMesh> ArtSlotCachedPlane;
	TMap<FString, TWeakObjectPtr<UTexture2D>> ArtSlotCachedTextures;
	int32 ArtSlotLoadCalls = 0;

	template <typename T>
	T* ArtSlotCachedLoad(TWeakObjectPtr<T>& Cache, const TCHAR* Path)
	{
		if (!Cache.IsValid())
		{
			++ArtSlotLoadCalls;
			Cache = LoadObject<T>(nullptr, Path, nullptr, LOAD_NoWarn | LOAD_Quiet);
		}
		return Cache.Get();
	}

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
	if (!Row.bStandInOk)
	{
		// visualqa: an unkeyed or framed stand-in draws as a box on the play screen; the plain stand-in (or nothing) wins.
		return { Passed + TEXT(".") + Row.Asset };
	}
	return { Passed + TEXT(".") + Row.Asset, Placeholder + TEXT(".") + Row.Asset + UmbrellaArtSlotConst::PlaceholderSuffix };
}

UTexture2D* ArtSlot::LoadTexture(const FArtSlotRow& Row)
{
	// Hits are cached per path; a miss is not, so an asset imported later in the session is still found.
	for (const FString& Path : TexturePaths(Row))
	{
		TWeakObjectPtr<UTexture2D>& Cached = ArtSlotCachedTextures.FindOrAdd(Path);
		if (!Cached.IsValid())
		{
			++ArtSlotLoadCalls;
			Cached = LoadObject<UTexture2D>(nullptr, *Path, nullptr, LOAD_NoWarn | LOAD_Quiet);
		}
		if (Cached.IsValid())
		{
			return Cached.Get();
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
	UMaterialInterface* Material = ArtSlotCachedLoad(ArtSlotCachedMaterial, UmbrellaArtSlotConst::MaterialPath);
	UStaticMesh* Plane = Material ? ArtSlotCachedLoad(ArtSlotCachedPlane, UmbrellaArtSlotConst::PlanePath) : nullptr;
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
	// A packed sheet shows one cell: U is cut by Cols in the material, V by Rows here (the top row; V runs down the picture).
	Dynamic->SetScalarParameterValue(ArtSlotTileVParam, RepeatsV / static_cast<float>(FMath::Max(1, Row.Rows)));
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
	Mesh->ComponentTags.Remove(ArtSlotTag);
	Mesh->SetCastShadow(false);
}

bool ArtSlot::IsUnlit(const UStaticMeshComponent* Mesh)
{
	const UMaterialInterface* Material = IsValid(Mesh) ? Mesh->GetMaterial(0) : nullptr;
	const UMaterial* Base = Material ? Material->GetMaterial() : nullptr;
	return Base && Base->GetShadingModels().HasOnlyShadingModel(MSM_Unlit);
}

int32 ArtSlot::LoadCallCount()
{
	return ArtSlotLoadCalls;
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

void ArtSlot::SetTexture(UStaticMeshComponent* Mesh, UTexture2D* Texture, const FArtSlotRow& Row)
{
	if (UMaterialInstanceDynamic* Dynamic = IsValid(Mesh) && IsValid(Texture) ? Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(0)) : nullptr)
	{
		Dynamic->SetTextureParameterValue(ArtSlotParam, Texture);
		Dynamic->SetScalarParameterValue(ArtSlotColsParam, static_cast<float>(FMath::Max(1, Row.Cols)));
		Dynamic->SetScalarParameterValue(ArtSlotFrameParam, 0.0f);
		if (!Row.bTile)
		{
			Dynamic->SetScalarParameterValue(ArtSlotTileUParam, 1.0f);
			Dynamic->SetScalarParameterValue(ArtSlotTileVParam, 1.0f / static_cast<float>(FMath::Max(1, Row.Rows)));
		}
	}
}

float ArtSlot::CellAspect(const UTexture2D* Texture, const FArtSlotRow& Row)
{
	const float Width = IsValid(Texture) ? static_cast<float>(Texture->GetSizeX()) / FMath::Max(1, Row.Cols) : 0.0f;
	const float Height = IsValid(Texture) ? static_cast<float>(Texture->GetSizeY()) / FMath::Max(1, Row.Rows) : 0.0f;
	return (Width > 0.0f && Height > 0.0f) ? Width / Height : 1.0f;
}

bool ArtSlot::IsDrawingArt(const UStaticMeshComponent* Mesh)
{
	const UMaterialInstanceDynamic* Dynamic = IsValid(Mesh) ? Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(0)) : nullptr;
	// The flat unlit stand-in uses the same material; only Apply tags a component as drawing a picture.
	return Dynamic && Mesh->ComponentHasTag(ArtSlotTag) && Dynamic->Parent && Dynamic->Parent->GetPathName() == UmbrellaArtSlotConst::MaterialPath;
}

void ArtSlot::SetFrame(UStaticMeshComponent* Mesh, int32 Frame)
{
	if (UMaterialInstanceDynamic* Dynamic = IsValid(Mesh) ? Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(0)) : nullptr)
	{
		Dynamic->SetScalarParameterValue(ArtSlotFrameParam, static_cast<float>(Frame));
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

FLinearColor ArtSlot::GetTint(const UStaticMeshComponent* Mesh)
{
	FLinearColor Tint = FLinearColor::White;
	if (const UMaterialInstanceDynamic* Dynamic = IsValid(Mesh) ? Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(0)) : nullptr)
	{
		Dynamic->GetVectorParameterValue(FMaterialParameterInfo(ArtSlotTintParam), Tint);
	}
	return Tint;
}

void ArtSlot::SetTint(UStaticMeshComponent* Mesh, const FLinearColor& Tint)
{
	if (UMaterialInstanceDynamic* Dynamic = IsValid(Mesh) ? Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(0)) : nullptr)
	{
		if (Dynamic->Parent && Dynamic->Parent->GetPathName() == UmbrellaArtSlotConst::MaterialPath)
		{
			Dynamic->SetVectorParameterValue(ArtSlotTintParam, Tint);
		}
	}
}

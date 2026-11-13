#include "Feedback/Art/ArtSlot.h"
#include "BrokenMill/BrokenMillPlaceholder.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"

namespace
{
	const TCHAR* BrokenMillCubePath = TEXT("/Engine/BasicShapes/Cube.Cube");
	const TCHAR* BrokenMillShapeMaterialPath = TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");
	const FName BrokenMillColorParameter(TEXT("Color"));
}

void BrokenMillPlaceholder::ApplyCube(UStaticMeshComponent* Visual, UObject* Outer, const FVector2D& Size, const FLinearColor& Color, float CubeSize, float DepthScale)
{
	if (!Visual || CubeSize <= 0.0f)
	{
		return;
	}
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, BrokenMillCubePath, nullptr, LOAD_NoWarn | LOAD_Quiet);
	if (!Cube)
	{
		return;
	}
	Visual->SetStaticMesh(Cube);
	Visual->SetRelativeScale3D(FVector(Size.X / CubeSize, DepthScale, Size.Y / CubeSize));
	if (ArtSlot::ApplyFlatUnlit(Visual, Outer, Color))
	{
		return;
	}
	if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, BrokenMillShapeMaterialPath, nullptr, LOAD_NoWarn | LOAD_Quiet))
	{
		UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(Base, Outer);
		Material->SetVectorParameterValue(BrokenMillColorParameter, Color);
		Visual->SetMaterial(0, Material);
	}
}

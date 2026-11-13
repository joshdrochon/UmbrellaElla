#pragma once

#include "CoreMinimal.h"

class UMaterialInterface;
class UStaticMeshComponent;
class UTexture2D;

/** One shipped visual and the asset it is drawn from (rows generated from docs/build/art-inventory.csv). */
struct FArtSlotRow
{
	const TCHAR* Visual;
	const TCHAR* Folder;
	/** Asset base name with its prefix (T_Paper); the game loads it, then "<Asset>_PH", else keeps the stand-in. */
	const TCHAR* Asset;
	/** Frames in one row of the sheet (1 = a single picture). */
	int32 Cols;
	/** True when the picture tiles across the panel (paper). */
	bool bTile;
	/** The class that loads this slot today; "-" = nothing draws it yet. */
	const TCHAR* DrawnBy;
};

/** What a draw request did. NoTexture and NoMaterial leave the stand-in untouched. */
enum class EArtSlotDraw : uint8
{
	Drawn,
	NoTexture,
	NoMaterial
};

namespace UmbrellaArtSlotConst
{
	static const TCHAR* const GameRoot = TEXT("/Game/UmbrellaElla/Art");
	static const TCHAR* const PlaceholderSuffix = TEXT("_PH");
	/** The one unlit masked material every slot is drawn with (tools/build/assets/art_slot_material.py makes it). */
	static const TCHAR* const MaterialPath = TEXT("/Game/UmbrellaElla/Art/Slots/M_ArtSlot_Unlit.M_ArtSlot_Unlit");
	static const TCHAR* const PlanePath = TEXT("/Engine/BasicShapes/Plane.Plane");
	/** Engine plane edge in units. */
	static constexpr float PlaneEdge = 100.0f;
	/** World units one repeat of a tiled picture covers. */
	static constexpr float TileWorldSize = 600.0f;
}

/**
 * Art slots: draw a texture on an unlit masked quad in place of a stand-in cube, keep the stand-in when the asset is
 * missing. Visual only: the component never gets collision (rule: no collision).
 */
namespace ArtSlot
{
	/** Every row of the catalogue. Pure. */
	UMBRELLAELLA_API TConstArrayView<FArtSlotRow> Rows();

	/** Row for a visual id such as "ella-state:Idle"; null when unknown. Pure. */
	UMBRELLAELLA_API const FArtSlotRow* Find(const TCHAR* Visual);

	/** Object paths tried in order: the passed asset, then its _PH placeholder. Pure. */
	UMBRELLAELLA_API TArray<FString> TexturePaths(const FArtSlotRow& Row);

	/** The slot path without suffix, e.g. /Game/UmbrellaElla/Art/Scene/T_Paper. Pure. */
	UMBRELLAELLA_API FString SlotPath(const FArtSlotRow& Row);

	/** First texture that loads for the row, or null. */
	UMBRELLAELLA_API UTexture2D* LoadTexture(const FArtSlotRow& Row);

	/** Plane scale that fills the same width and height as a stand-in box scale (X, Y, Z). Pure. */
	UMBRELLAELLA_API FVector PlaneScaleFor(const FVector& BoxScale);

	/**
	 * Draw Texture on Mesh: swap its shape for a camera-facing plane, put the unlit masked material on it, and keep the
	 * footprint of the box scale the stand-in had. Anything but Drawn leaves the stand-in untouched.
	 */
	UMBRELLAELLA_API EArtSlotDraw Apply(UStaticMeshComponent* Mesh, UTexture2D* Texture, const FArtSlotRow& Row, const FVector& BoxScale);

	/** Load the row's texture and Apply it (NoTexture when no asset exists). */
	UMBRELLAELLA_API EArtSlotDraw ApplyRow(UStaticMeshComponent* Mesh, const FArtSlotRow& Row, const FVector& BoxScale);

	/** Swap the picture on a component already drawn with art (a state change). */
	UMBRELLAELLA_API void SetTexture(UStaticMeshComponent* Mesh, UTexture2D* Texture);

	/** True once Apply put art on the component. */
	UMBRELLAELLA_API bool HasArt(const UStaticMeshComponent* Mesh);

	/** Same as SetBoxScale, in world scale (a component whose parent is not unit scale). */
	UMBRELLAELLA_API void SetWorldBoxScale(UStaticMeshComponent* Mesh, const FVector& BoxScale);

	/** Re-size: a box scale for a stand-in, or the matching plane scale when art is drawn. */
	UMBRELLAELLA_API void SetBoxScale(UStaticMeshComponent* Mesh, const FVector& BoxScale);
}

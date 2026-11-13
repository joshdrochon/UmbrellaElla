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
	/** Frames in one row of the sheet (1 = a single picture; tools/build/art_slots.py reads packed stand-in sheets). */
	int32 Cols;
	/** True when the picture tiles across the panel (paper). */
	bool bTile;
	/** The class that loads this slot today; "-" = nothing draws it yet. */
	const TCHAR* DrawnBy;
	/** Rows of frames in the sheet (a stand-in cut as a 6x4 grid has 4); the slot draws the top row, frame 0 first. */
	int32 Rows = 1;
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
	static const TCHAR* const MaterialPath = TEXT("/Game/UmbrellaElla/Materials/M_ArtSlot_Unlit.M_ArtSlot_Unlit");
	static const TCHAR* const PlanePath = TEXT("/Engine/BasicShapes/Plane.Plane");
	/** Engine plane edge in units. */
	static constexpr float PlaneEdge = 100.0f;
	/** World units one repeat of a tiled picture covers. */
	static constexpr float TileWorldSize = 600.0f;
	/** Engine white texture: the flat unlit stand-in colour is this times the slot material's Tint. */
	static const TCHAR* const WhiteTexturePath = TEXT("/Engine/EngineResources/WhiteSquareTexture.WhiteSquareTexture");
	/** Stand-in colour when a site has none of its own (paper grey-brown, art bible palette family). */
	static const FLinearColor StandInDefaultColor(0.80f, 0.68f, 0.45f, 1.0f);
	/** Role colours for stand-ins, so Ella, enemies and the Keeper read apart against the dark paper backdrop. */
	static const FLinearColor StandInEllaColor(0.95f, 0.85f, 0.35f, 1.0f);
	static const FLinearColor StandInEnemyColor(0.85f, 0.28f, 0.22f, 1.0f);
	static const FLinearColor StandInKeeperColor(0.55f, 0.40f, 0.75f, 1.0f);
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

	/** How many asset loads the slot code has run (cache misses). Tests read it to prove repeat draws load nothing. */
	UMBRELLAELLA_API int32 LoadCallCount();

	/** Load the row's texture and Apply it (NoTexture when no asset exists). */
	UMBRELLAELLA_API EArtSlotDraw ApplyRow(UStaticMeshComponent* Mesh, const FArtSlotRow& Row, const FVector& BoxScale);

	/**
	 * Flat unlit stand-in colour (screenfix): put the unlit slot material tinted Color on Mesh, so a placeholder cube
	 * never depends on level lights (art bible: unlit sprite materials only). Leaves the component as it was when the
	 * material is missing (IsUnlit then says false).
	 */
	UMBRELLAELLA_API void SetFlatUnlit(UStaticMeshComponent* Mesh, UObject* Outer, const FLinearColor& Color);

	/** True when the component's material 0 is the unlit slot material (or an instance of it). */
	UMBRELLAELLA_API bool IsUnlit(const UStaticMeshComponent* Mesh);

	/** Swap the picture on a component already drawn with art (a state change). */
	UMBRELLAELLA_API void SetTexture(UStaticMeshComponent* Mesh, UTexture2D* Texture);

	/** Swap the picture and its sheet layout (Cols, Rows; back to frame 0), for pictures cut differently (screenfix B2). */
	UMBRELLAELLA_API void SetTexture(UStaticMeshComponent* Mesh, UTexture2D* Texture, const FArtSlotRow& Row);

	/** Width / height of one cell of the row's sheet in Texture (1 when the size is unknown). Pure read. */
	UMBRELLAELLA_API float CellAspect(const UTexture2D* Texture, const FArtSlotRow& Row);

	/** True while the component's material is the art-slot material (false once something else, such as a stand-in refresh, replaced it). Pure read. */
	UMBRELLAELLA_API bool IsDrawingArt(const UStaticMeshComponent* Mesh);

	/** Show one cell of a sheet drawn with art (a row with Cols > 1). */
	UMBRELLAELLA_API void SetFrame(UStaticMeshComponent* Mesh, int32 Frame);

	/** True once Apply put art on the component. */
	UMBRELLAELLA_API bool HasArt(const UStaticMeshComponent* Mesh);

	/** Same as SetBoxScale, in world scale (a component whose parent is not unit scale). */
	UMBRELLAELLA_API void SetWorldBoxScale(UStaticMeshComponent* Mesh, const FVector& BoxScale);

	/** Re-size: a box scale for a stand-in, or the matching plane scale when art is drawn. */
	UMBRELLAELLA_API void SetBoxScale(UStaticMeshComponent* Mesh, const FVector& BoxScale);
}

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "FrameCompositionSubsystem.generated.h"

class UStaticMeshComponent;

namespace UmbrellaFrameConst
{
	/**
	 * Everything drawn behind the play layer (world Y below this) is dimmed toward the Other Realm study's dark
	 * backdrop (visualqa, Josh 16:05). Between the arena depth and the hazard depth (UmbrellaDrawOrder).
	 */
	static constexpr float BehindPlayY = -150.0f;
	/** Multiply on backdrop art: the study's near-black, warm ground (#1c1a18 range), the picture's detail kept faint. */
	static const FLinearColor BackdropDim(0.055f, 0.048f, 0.042f, 1.0f);
	/** A flat stand-in panel behind play is never brighter than this (sRGB about #1c1a18). */
	static const FLinearColor BackdropFlat(0.012f, 0.011f, 0.010f, 1.0f);
	/** Cream route blocks become the study's floating-island umber (sRGB about #3a2a1c). */
	static const FLinearColor IslandUmber(0.042f, 0.023f, 0.012f, 1.0f);
	/**
	 * Salmon enemy stand-in boxes become a dark ink red (sRGB about #3a1418, the shot-red family at its darkest): a small
	 * dark figure as in the study, never a pink or red block (artella r38, lead 17:18).
	 */
	static const FLinearColor EnemyShadow(0.042f, 0.007f, 0.009f, 1.0f);
	/** Enemy stand-ins are drawn at this share of their box (visual only; the hitbox is unchanged). */
	static constexpr float EnemyStandInScale = 0.6f;
	/**
	 * The Keeper's attack telegraph and gust cue cubes (AKeeperOfTime): drawn as thin lines, never boxes (the 1050x120
	 * telegraph was the pink block over Ella, lead 17:08). The telegraph is shot red #ff3658, the gust ash blue #555e60.
	 */
	static const TCHAR* const KeeperTelegraphName = TEXT("TelegraphVisual");
	static const TCHAR* const KeeperGustName = TEXT("GustVisual");
	static const FLinearColor TelegraphRed(1.0f, 0.037f, 0.095f, 1.0f);
	static const FLinearColor GustAsh(0.091f, 0.111f, 0.117f, 1.0f);
	/** Share of its height a telegraph or gust cue keeps (120 units -> about 18: a line, still readable). */
	static constexpr float CueLineShare = 0.15f;
	/**
	 * Backdrop pictures artscene ships graded to the study (bg-layer:* panels, bg:* scene panels): never dimmed again
	 * (artscene request 5: the dim turned the graded route black, luma p50 0 against the study's 35).
	 */
	static const TCHAR* const GradedBackdropNames[] = { TEXT("BackdropPanel"), TEXT("ScenePanel") };
	/**
	 * Name of the Keeper's stand-in body (on the Keeper actor) and of the arena's Keeper square. Only the arena's square
	 * is ever hidden; the Keeper actor itself is always drawn (lead 17:08).
	 */
	static const TCHAR* const KeeperStandInName = TEXT("KeeperStandIn");
	/** Ella's stand-in figure (UEllaAnimPresenterComponent) when no Ella art draws. */
	static const TCHAR* const EllaStandInName = TEXT("EllaStandIn");
	/** Lilac Keeper stand-ins become the GDD's fabricated metal: a gunmetal silhouette (sRGB about #5a554e). */
	static const FLinearColor KeeperMetal(0.102f, 0.090f, 0.076f, 1.0f);
	/** Ella's stand-in reads as the study's small dark figure, never a bright block (sRGB about #4a3f36). */
	static const FLinearColor EllaInk(0.069f, 0.050f, 0.037f, 1.0f);
	/** Colour match tolerances: a tint already applied, and a stand-in role colour. */
	static constexpr float AppliedTolerance = 0.0005f;
	static constexpr float RoleTolerance = 0.002f;
	/** With -VisualQADump on the command line, every visible mesh is logged (LogUmbrellaFrame) this often, in seconds. */
	static constexpr float DumpInterval = 5.0f;
	/** Seconds between passes over new actors and the meshes this subsystem changed. */
	static constexpr float PassInterval = 0.2f;
	/** Seconds between full passes over every actor (catches components added to old actors). */
	static constexpr float FullPassInterval = 2.0f;
	/** A newly spawned actor is looked at on this many passes (its presenters add components over the first ticks). */
	static constexpr int32 NewActorPasses = 5;
	/**
	 * Camera margin (coordinator 16:20): world units shown above the top of Ella's picture cell when she is at the play
	 * ceiling (arena top minus capsule half-height, z 1036 at HeroSize 1). The ceiling itself is unchanged.
	 */
	static constexpr float CeilingSpritePad = 8.0f;
	/**
	 * B11 (agentplay 67011eb2): in Director's Cut the "Director's Cut" title sits in this top share of the view. The
	 * camera margin keeps Ella's whole picture below it at the play ceiling, so the title never draws over her.
	 */
	static constexpr float TitleBandShare = 0.05f;
	/** Side of the engine cube/plane the art boxes scale (ArtSlot), world units. */
	static constexpr float UnitBoxSize = 100.0f;
	/** An orthographic width within this of the expected one counts as unchanged (another system's zoom is left alone). */
	static constexpr float OrthoMatchTolerance = 0.5f;
}

class ACharacter;
class AUmbrellaArena;

/** What the frame pass does to one mesh. */
enum class EFrameTreatment : uint8
{
	Keep,
	DimBackdropArt,
	DarkenBackdropPanel,
	TintIsland,
	TintEnemy,
	TintKeeper,
	TintElla,
	TelegraphLine,
	GustLine,
	Hide
};

/** What the frame pass knows about one mesh. */
struct FFrameMeshFacts
{
	FName ComponentName;
	float WorldY = 0.0f;
	bool bDrawsArt = false;
	bool bSlotMaterial = true;
	/** The mesh's own tint before this subsystem changed it. */
	FLinearColor Tint = FLinearColor::White;
	/** The mesh belongs to the arena (its Keeper square), not to the Keeper actor. */
	bool bArenaOwned = false;
};

/**
 * Composes the gameplay frame toward the Other Realm study: dims the backdrop, turns cream stand-in blocks into
 * dark island umber and hides lilac Keeper stand-in cubes, so no bright placeholder box or bar is ever on a gameplay
 * screen. Visual only (tint and hidden-in-game); never collision, size or game state. visualqa lane.
 */
UCLASS()
class UMBRELLAELLA_API UFrameCompositionSubsystem final : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

	virtual void PostInitialize() override;
	virtual void Deinitialize() override;

	/** The treatment for a mesh with these facts (Tint = its own tint, before any frame treatment). Pure. */
	static EFrameTreatment TreatmentFor(const FFrameMeshFacts& Facts);

	/** The colour a tint treatment sets (White for Keep/Hide). Pure. */
	static FLinearColor TintFor(EFrameTreatment Treatment);

	/** The share of its own size (per axis) a treated mesh is drawn at (1 = unchanged). Pure. */
	static FVector ScaleFor(EFrameTreatment Treatment);

	/** Apply the treatment to every mesh in the world now; returns how many meshes changed. */
	int32 ComposeNow();

	/** Put every mesh this subsystem changed back to its own tint and visibility; returns how many. */
	int32 RestoreAll();

	/** Meshes currently changed by the frame pass. */
	int32 TouchedCount() const { return Touched.Num(); }

	/** How many actors the last pass looked at (a full pass looks at all; a quick pass at new ones only). */
	int32 LastPassActorCount() const { return LastActorCount; }

	/** One frame pass: new actors and changed meshes, or every actor when bFull. Returns how many meshes changed. */
	int32 ComposePass(bool bFull);

	/** Log every rendered mesh: owner, component, world box, art or stand-in tint (finds the boxes on a capture). */
	int32 DumpVisibleMeshes() const;

	/** Half-height of Ella's drawn picture cell for an actor scale (UmbrellaPresenterConst::ArtCellHeight). Pure. */
	static float SpriteHalfHeight(float ActorScaleZ);

	/**
	 * Orthographic width that keeps the arena's full height plus Overhang above and below on screen, and (TopShare > 0)
	 * Ella's picture at the ceiling below the top TopShare of the view (a HUD title band). Pure.
	 */
	static float MarginOrthoWidth(float ArenaHeight, float AspectRatio, float SpriteHalf, float CapsuleHalf, float TopShare = 0.0f);

	/** World Z of the top edge of an orthographic view. Pure. */
	static float FrameTopZ(float CameraZ, float OrthoWidth, float AspectRatio);

	/**
	 * Widen the arena camera so Ella's whole picture stays in frame at the play ceiling, in Start Game and Director's
	 * Cut. Leaves a camera another system zoomed (VFX demo capture) alone.
	 */
	void ApplyCameraMargin(AUmbrellaArena* Arena, const ACharacter* Ella, bool bTitleBand = false);

protected:
	virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override;

private:
	struct FFrameOriginal
	{
		FLinearColor Tint = FLinearColor::White;
		/** The tint this subsystem last set (so an owner's own recolour is told apart from ours). */
		FLinearColor Applied = FLinearColor::White;
		/** The mesh's own relative scale, and the one this subsystem last set. */
		FVector Scale = FVector::OneVector;
		FVector AppliedScale = FVector::OneVector;
		bool bHiddenInGame = false;
		bool bDrawsArt = false;
	};

	void HandleActorSpawned(AActor* Actor);
	int32 ComposeMesh(UStaticMeshComponent* Mesh);
	AUmbrellaArena* FindArena();

	TMap<TWeakObjectPtr<UStaticMeshComponent>, FFrameOriginal> Touched;
	TMap<TWeakObjectPtr<AActor>, int32> NewActors;
	TWeakObjectPtr<AUmbrellaArena> CachedArena;
	FDelegateHandle SpawnHandle;
	int32 LastActorCount = 0;
	bool bPassedOnce = false;
	float SinceFullPass = 0.0f;
	float LastMarginOrthoWidth = 0.0f;
	float SinceLastPass = 0.0f;
	float SinceLastDump = 0.0f;
};

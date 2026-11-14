#include "Arena/UmbrellaArena.h"
#include "Feedback/Art/ArtSlot.h"
#include "Camera/CameraComponent.h"
#include "Components/BoxComponent.h"
#include "Core/UmbrellaCollision.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Level/LevelCatalogue.h"

namespace
{
	/** Wall box helper: invisible blocking box in the play plane. */
	UBoxComponent* MakeBox(AActor* Owner, USceneComponent* Parent, const TCHAR* Name, const FName Profile)
	{
		UBoxComponent* Box = Owner->CreateDefaultSubobject<UBoxComponent>(Name);
		Box->SetupAttachment(Parent);
		Box->SetCollisionProfileName(Profile);
		return Box;
	}

	/** Walls and ceiling stop shots (lead call B): Block on both shot channels. */
	void BlockShots(UBoxComponent* Box)
	{
		Box->SetCollisionResponseToChannel(UmbrellaCollision::PlayerShot, ECR_Block);
		Box->SetCollisionResponseToChannel(UmbrellaCollision::EnemyShot, ECR_Block);
	}
}

AUmbrellaArena::AUmbrellaArena()
{
	PrimaryActorTick.bCanEverTick = true;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;

	PlayCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("PlayCamera"));
	PlayCamera->SetupAttachment(Root);

	LeftWall = MakeBox(this, Root, TEXT("LeftWall"), TEXT("BlockAllDynamic"));
	RightWall = MakeBox(this, Root, TEXT("RightWall"), TEXT("BlockAllDynamic"));
	Ceiling = MakeBox(this, Root, TEXT("Ceiling"), TEXT("BlockAllDynamic"));
	BlockShots(LeftWall);
	BlockShots(RightWall);
	BlockShots(Ceiling);
	LethalBottom = MakeBox(this, Root, TEXT("LethalBottom"), TEXT("OverlapAllDynamic"));
	LethalBottom->ComponentTags.Add(TEXT("LethalBottom"));

	const FArenaCameraTuning& T = GetDefault<UUmbrellaTuning>()->ArenaCamera;
	const float HalfW = T.ArenaWidth * 0.5f;
	const float HalfH = T.ArenaHeight * 0.5f;
	const float Wall = T.WallThickness;
	// The arena origin is the bottom-left corner of the play area; X right, Z up.
	LeftWall->SetRelativeLocation(FVector(-Wall * 0.5f, 0.0f, HalfH));
	LeftWall->SetBoxExtent(FVector(Wall * 0.5f, Wall, HalfH + Wall));
	RightWall->SetRelativeLocation(FVector(T.ArenaWidth + Wall * 0.5f, 0.0f, HalfH));
	RightWall->SetBoxExtent(FVector(Wall * 0.5f, Wall, HalfH + Wall));
	Ceiling->SetRelativeLocation(FVector(HalfW, 0.0f, T.ArenaHeight + Wall * 0.5f));
	Ceiling->SetBoxExtent(FVector(HalfW + Wall, Wall, Wall * 0.5f));
	LethalBottom->SetRelativeLocation(FVector(HalfW, 0.0f, -Wall * 0.5f));
	LethalBottom->SetBoxExtent(FVector(HalfW + Wall, Wall, Wall * 0.5f));

	// Orthographic fixed 16:9 camera looking down -Y so larger Y is nearer (UmbrellaDrawOrder).
	PlayCamera->SetProjectionMode(ECameraProjectionMode::Orthographic);
	PlayCamera->SetOrthoWidth(T.ArenaWidth);
	PlayCamera->SetConstraintAspectRatio(true);
	PlayCamera->bAutoCalculateOrthoPlanes = false;
	PlayCamera->SetAspectRatio(T.CameraAspectRatio);
	PlayCamera->SetRelativeLocation(FVector(HalfW, T.CameraDistance, HalfH));
	PlayCamera->SetRelativeRotation(FRotator(0.0, UmbrellaArenaConst::CameraYaw, 0.0));
	ApplyFlatLookPostProcess(PlayCamera->PostProcessSettings);
	PlayCamera->PostProcessBlendWeight = 1.0f;
}

void AUmbrellaArena::ApplyFlatLookPostProcess(FPostProcessSettings& Settings)
{
	// Unlit 2D look: a fixed exposure (no eye adaptation brightening a dark frame), no bloom, blur or vignette.
	Settings.bOverride_AutoExposureMethod = true;
	Settings.AutoExposureMethod = AEM_Histogram;
	Settings.bOverride_AutoExposureMinBrightness = true;
	Settings.AutoExposureMinBrightness = UmbrellaArenaConst::FixedExposureBrightness;
	Settings.bOverride_AutoExposureMaxBrightness = true;
	Settings.AutoExposureMaxBrightness = UmbrellaArenaConst::FixedExposureBrightness;
	Settings.bOverride_AutoExposureBias = true;
	Settings.AutoExposureBias = 0.0f;
	Settings.bOverride_BloomIntensity = true;
	Settings.BloomIntensity = 0.0f;
	Settings.bOverride_MotionBlurAmount = true;
	Settings.MotionBlurAmount = 0.0f;
	Settings.bOverride_VignetteIntensity = true;
	Settings.VignetteIntensity = 0.0f;
	Settings.bOverride_AmbientOcclusionIntensity = true;
	Settings.AmbientOcclusionIntensity = 0.0f;
	Settings.bOverride_SceneFringeIntensity = true;
	Settings.SceneFringeIntensity = 0.0f;
	Settings.bOverride_FilmGrainIntensity = true;
	Settings.FilmGrainIntensity = 0.0f;
	Settings.bOverride_LensFlareIntensity = true;
	Settings.LensFlareIntensity = 0.0f;
}

FVector AUmbrellaArena::LocalPoint(float XFraction, float ZFraction) const
{
	const FArenaCameraTuning& T = GetDefault<UUmbrellaTuning>()->ArenaCamera;
	return GetActorTransform().TransformPosition(FVector(T.ArenaWidth * XFraction, UmbrellaDrawOrder::EllaY, T.ArenaHeight * ZFraction));
}

FVector AUmbrellaArena::GetPlayerStartLocation() const
{
	const FArenaCameraTuning& T = GetDefault<UUmbrellaTuning>()->ArenaCamera;
	return LocalPoint(T.PlayerStartXFraction, T.PlayerStartZFraction);
}

FVector AUmbrellaArena::GetKeeperAnchorLocation() const
{
	const FArenaCameraTuning& T = GetDefault<UUmbrellaTuning>()->ArenaCamera;
	FVector Point = LocalPoint(T.KeeperAnchorXFraction, T.KeeperAnchorZFraction);
	Point.Y = GetActorLocation().Y + UmbrellaDrawOrder::KeeperY;
	return Point;
}

bool AUmbrellaArena::HasWrappedAfterAdvance(float& Offset, float Speed, float DeltaTime, float Period)
{
	if (Period <= 0.0f)
	{
		return false;
	}
	Offset += Speed * DeltaTime;
	if (Offset >= Period)
	{
		Offset = FMath::Fmod(Offset, Period);
		return true;
	}
	return false;
}

void AUmbrellaArena::BuildPlaceholders()
{
	UStaticMesh* Shape = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	const FArenaCameraTuning& T = GetDefault<UUmbrellaTuning>()->ArenaCamera;
	const float HalfW = T.ArenaWidth * 0.5f;
	const float HalfH = T.ArenaHeight * 0.5f;
	const auto Make = [this, Shape](const TCHAR* Name, const FVector& Location, const FVector& Scale) -> UStaticMeshComponent*
	{
		UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(this, Name);
		if (IsValid(Shape))
		{
			Mesh->SetStaticMesh(Shape);
		}
		Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Mesh->SetupAttachment(RootComponent);
		Mesh->SetRelativeLocation(Location);
		Mesh->SetRelativeScale3D(Scale);
		ArtSlot::SetFlatUnlit(Mesh, this, FCString::Strstr(Name, TEXT("Keeper")) ? UmbrellaArtSlotConst::StandInKeeperColor : UmbrellaArenaConst::BackgroundStandInColor);
		Mesh->RegisterComponent();
		return Mesh;
	};
	// Cube is 100 units; scale = size / 100.
	const float Unit = UmbrellaArenaConst::CubeSize;
	BackgroundFar = Make(TEXT("BackgroundFar"), FVector(HalfW, UmbrellaDrawOrder::BackgroundFarY, HalfH), FVector(T.ArenaWidth * T.BackgroundWidthScale / Unit, UmbrellaArenaConst::PlaneThickness, T.ArenaHeight / Unit));
	BackgroundNear = Make(TEXT("BackgroundNear"), FVector(HalfW, UmbrellaDrawOrder::BackgroundNearY, HalfH * 0.5f), FVector(T.ArenaWidth * T.BackgroundWidthScale / Unit, UmbrellaArenaConst::PlaneThickness, T.ArenaHeight * 0.5f / Unit));
	KeeperStandIn = Make(TEXT("KeeperStandIn"), FVector(T.ArenaWidth * T.KeeperAnchorXFraction, UmbrellaDrawOrder::KeeperY, T.ArenaHeight * T.KeeperAnchorZFraction), FVector(T.KeeperStandInSize / Unit, UmbrellaArenaConst::KeeperDepthScale, T.KeeperStandInSize / Unit));
	KeeperStandIn->SetVisibility(!bKeeperArtShown);
	ApplyScroll();
}

void AUmbrellaArena::SetKeeperArtShown(bool bShown)
{
	bKeeperArtShown = bShown;
	if (KeeperStandIn)
	{
		KeeperStandIn->SetVisibility(!bShown);
	}
}

void AUmbrellaArena::BeginPlay()
{
	Super::BeginPlay();
	BuildPlaceholders();
}

void AUmbrellaArena::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const FArenaCameraTuning& T = GetDefault<UUmbrellaTuning>()->ArenaCamera;
	if (HasWrappedAfterAdvance(FarOffset, T.BackgroundFarSpeed, DeltaSeconds, T.ArenaWidth))
	{
		BroadcastLooped(TEXT("Far"));
	}
	if (HasWrappedAfterAdvance(NearOffset, T.BackgroundNearSpeed, DeltaSeconds, T.ArenaWidth))
	{
		BroadcastLooped(TEXT("Near"));
	}
	ApplyScroll();
}

void AUmbrellaArena::BroadcastLooped(FName Layer) const
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::BackgroundLooped;
		Event.SourceId = GetFName();
		Event.Detail = Layer;
		Bus->Broadcast(Event);
	}
}

float AUmbrellaArena::PlaneCenterX(float Offset, float ArenaWidth, float WidthScale)
{
	// The plane spans [-Offset, -Offset + ArenaWidth * WidthScale]; with scale >= 2 and Offset < ArenaWidth it covers [0, ArenaWidth].
	return -Offset + ArenaWidth * WidthScale * 0.5f;
}

void AUmbrellaArena::ApplyScroll()
{
	const FArenaCameraTuning& T = GetDefault<UUmbrellaTuning>()->ArenaCamera;
	const auto Move = [&T](UStaticMeshComponent* Plane, float Offset)
	{
		if (IsValid(Plane))
		{
			FVector Location = Plane->GetRelativeLocation();
			Location.X = PlaneCenterX(Offset, T.ArenaWidth, T.BackgroundWidthScale);
			Plane->SetRelativeLocation(Location);
		}
	};
	Move(BackgroundFar, FarOffset);
	Move(BackgroundNear, NearOffset);
}

void AUmbrellaArena::FollowEllaX(float EllaX, int32 TravelDirection)
{
	if (!IsFeatureEnabled(EFeatureId::CAM_08))
	{
		return;
	}
	const float ViewWidth = GetDefault<UUmbrellaTuning>()->ArenaCamera.ArenaWidth;
	const float Centre = CameraRules::ScrollCentreX(EllaX, TravelDirection, ViewWidth, 0.0f, LevelCatalogue::RouteLength());
	FVector Location = PlayCamera->GetComponentLocation();
	Location.X = Centre;
	PlayCamera->SetWorldLocation(Location);
}

void AUmbrellaArena::MovePlayArea(const FVector& Origin)
{
	SetActorLocation(Origin);
	const FArenaCameraTuning& T = GetDefault<UUmbrellaTuning>()->ArenaCamera;
	PlayCamera->SetRelativeLocation(FVector(T.ArenaWidth * 0.5f, T.CameraDistance, T.ArenaHeight * 0.5f));
}

bool AUmbrellaArena::IsCameraOnArenaFrame() const
{
	const FArenaCameraTuning& T = GetDefault<UUmbrellaTuning>()->ArenaCamera;
	return PlayCamera->GetRelativeLocation().Equals(FVector(T.ArenaWidth * 0.5f, T.CameraDistance, T.ArenaHeight * 0.5f));
}

#include "Arena/UmbrellaArena.h"
#include "Camera/CameraComponent.h"
#include "Components/BoxComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Kismet/GameplayStatics.h"

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
	PlayCamera->SetAspectRatio(T.CameraAspectRatio);
	PlayCamera->SetRelativeLocation(FVector(HalfW, T.CameraDistance, HalfH));
	PlayCamera->SetRelativeRotation(FRotator(0.0, UmbrellaArenaConst::CameraYaw, 0.0));
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

void AUmbrellaArena::BeginPlay()
{
	Super::BeginPlay();
	if (!IsFeatureEnabled(EFeatureId::CAM_03))
	{
		return;
	}
	APlayerController* Controller = UGameplayStatics::GetPlayerController(this, 0);
	if (IsValid(Controller))
	{
		Controller->SetViewTarget(this);
	}
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

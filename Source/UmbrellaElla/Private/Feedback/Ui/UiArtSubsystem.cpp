#include "Feedback/Ui/UiArtSubsystem.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Core/UmbrellaTuning.h"
#include "Feedback/Art/ArtSlot.h"
#include "Flow/UmbrellaPlayerController.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Styling/SlateBrush.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Layout/SScaleBox.h"

FString UUiArtSubsystem::VisualIdFor(EFlowScreen Screen)
{
	return FString::Printf(TEXT("screen:%s"), *StaticEnum<EFlowScreen>()->GetNameStringByValue(static_cast<int64>(Screen)));
}

bool UUiArtSubsystem::IsClickThrough() const
{
	return Widget.IsValid() && Widget->GetVisibility() == EVisibility::HitTestInvisible;
}

void UUiArtSubsystem::ClearScreenArt()
{
	if (Widget.IsValid() && GetWorld() && GetWorld()->GetGameViewport())
	{
		GetWorld()->GetGameViewport()->RemoveViewportWidgetContent(Widget.ToSharedRef());
	}
	Widget.Reset();
	Brush.Reset();
	ShownTexture.Reset();
	bHasTarget = false;
}

void UUiArtSubsystem::ShowScreenArt(EFlowScreen Screen, UTexture2D* Texture)
{
	ClearScreenArt();
	if (!IsValid(Texture) || !IsFeatureEnabled(EFeatureId::ART_08))
	{
		return;
	}
	ShownScreen = Screen;
	ShownTexture.Reset(Texture);
	Brush = MakeShared<FSlateBrush>();
	Brush->SetResourceObject(Texture);
	Brush->ImageSize = FVector2D(Texture->GetSizeX(), Texture->GetSizeY());
	Widget = SNew(SScaleBox)
		.Stretch(EStretch::Fill)
		.Visibility(EVisibility::HitTestInvisible)
		[
			SNew(SImage).Image(Brush.Get())
		];
	if (UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr)
	{
		Viewport->AddViewportWidgetContent(Widget.ToSharedRef(), GetDefault<UUmbrellaTuning>()->Flow.MenuContextPriority + UmbrellaUiArtConst::ZOrderAboveMenu);
	}
}

void UUiArtSubsystem::Tick(float DeltaTime)
{
	const AUmbrellaPlayerController* Controller = GetWorld() ? Cast<AUmbrellaPlayerController>(GetWorld()->GetFirstPlayerController()) : nullptr;
	if (!Controller)
	{
		return;
	}
	const EFlowScreen Screen = Controller->GetScreen();
	if (bHasTarget && TargetScreen == Screen)
	{
		return;
	}
	// One lookup per screen change; the loader cache keeps a repeat visit free.
	bHasTarget = true;
	TargetScreen = Screen;
	const FArtSlotRow* Row = ArtSlot::Find(*VisualIdFor(Screen));
	UTexture2D* Texture = Row ? ArtSlot::LoadTexture(*Row) : nullptr;
	ShowScreenArt(Screen, Texture);
	bHasTarget = true;
	TargetScreen = Screen;
}

void UUiArtSubsystem::Deinitialize()
{
	ClearScreenArt();
	Super::Deinitialize();
}

TStatId UUiArtSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UUiArtSubsystem, STATGROUP_Tickables);
}

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
#include "Widgets/Layout/SBox.h"
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

const UmbrellaUiPieceConst::FUiPiece* UUiArtSubsystem::FindPiece(const FString& Visual)
{
	for (const UmbrellaUiPieceConst::FUiPiece& Piece : UmbrellaUiPieceConst::Pieces)
	{
		if (Visual == Piece.Visual)
		{
			return &Piece;
		}
	}
	return nullptr;
}

void UUiArtSubsystem::ClearPieces()
{
	UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr;
	for (const TSharedPtr<SWidget>& Piece : PieceWidgets)
	{
		if (Viewport && Piece.IsValid())
		{
			Viewport->RemoveViewportWidgetContent(Piece.ToSharedRef());
		}
	}
	PieceWidgets.Reset();
	PieceBrushes.Reset();
	PieceTextures.Reset();
	ShownPieces.Reset();
}

bool UUiArtSubsystem::ShowPiece(const FString& Visual, EFlowScreen Screen, UTexture2D* Texture)
{
	const UmbrellaUiPieceConst::FUiPiece* Piece = FindPiece(Visual);
	if (!Piece || !(Piece->Screens & UiScreenBit(Screen)) || !IsValid(Texture) || !IsFeatureEnabled(EFeatureId::ART_08) || ShownPieces.Contains(Visual))
	{
		return false;
	}
	TSharedPtr<FSlateBrush> PieceBrush = MakeShared<FSlateBrush>();
	PieceBrush->SetResourceObject(Texture);
	PieceBrush->ImageSize = FVector2D(Texture->GetSizeX(), Texture->GetSizeY());
	TSharedPtr<SWidget> PieceWidget;
	if (Piece->bFill)
	{
		PieceWidget = SNew(SScaleBox).Stretch(EStretch::Fill).Visibility(EVisibility::HitTestInvisible)[SNew(SImage).Image(PieceBrush.Get())];
	}
	else
	{
		PieceWidget = SNew(SBox).HAlign(Piece->Horizontal).VAlign(Piece->Vertical).Visibility(EVisibility::HitTestInvisible)[SNew(SImage).Image(PieceBrush.Get())];
	}
	if (UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr)
	{
		const int32 Base = GetDefault<UUmbrellaTuning>()->Flow.MenuContextPriority;
		Viewport->AddViewportWidgetContent(PieceWidget.ToSharedRef(), Piece->bBelowMenu ? Base - 1 : Base + UmbrellaUiArtConst::ZOrderAboveMenu);
	}
	PieceWidgets.Add(PieceWidget);
	PieceBrushes.Add(PieceBrush);
	PieceTextures.Add(TStrongObjectPtr<UTexture2D>(Texture));
	ShownPieces.Add(Visual);
	return true;
}

void UUiArtSubsystem::ShowPiecesFor(EFlowScreen Screen)
{
	ClearPieces();
	for (const UmbrellaUiPieceConst::FUiPiece& Piece : UmbrellaUiPieceConst::Pieces)
	{
		if (!(Piece.Screens & UiScreenBit(Screen)))
		{
			continue;
		}
		const FArtSlotRow* Row = ArtSlot::Find(Piece.Visual);
		UTexture2D* Texture = Row ? ArtSlot::LoadTexture(*Row) : nullptr;
		ShowPiece(Piece.Visual, Screen, Texture);
	}
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
	ShowPiecesFor(Screen);
	bHasTarget = true;
	TargetScreen = Screen;
}

void UUiArtSubsystem::Deinitialize()
{
	ClearScreenArt();
	ClearPieces();
	Super::Deinitialize();
}

TStatId UUiArtSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UUiArtSubsystem, STATGROUP_Tickables);
}

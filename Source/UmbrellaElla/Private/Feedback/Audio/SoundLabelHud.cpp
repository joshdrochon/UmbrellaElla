#include "Feedback/Audio/SoundLabelHud.h"

#if UMBRELLAELLA_WORKBENCH

#include "Containers/Ticker.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Feedback/Audio/SoundLabelBoard.h"
#include "GameFramework/PlayerController.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputTriggers.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
	/** One row per possible line; each reads its line from the board on paint, so the list never rebuilds. */
	class SSoundLabelList final : public SCompoundWidget
	{
	public:
		SLATE_BEGIN_ARGS(SSoundLabelList) {}
			SLATE_ARGUMENT(TSharedPtr<FUmbrellaSoundLabelBoard>, Board)
		SLATE_END_ARGS()

		void Construct(const FArguments& InArgs)
		{
			Board = InArgs._Board;
			TSharedRef<SVerticalBox> Rows = SNew(SVerticalBox);
			for (int32 Row = 0; Row < UmbrellaSoundLabel::MaxLines; ++Row)
			{
				Rows->AddSlot().AutoHeight()
				[
					SNew(STextBlock)
					.Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), UmbrellaSoundLabel::FontSize))
					.ShadowOffset(FVector2D(1.0, 1.0))
					.Text_Lambda([this, Row]() { return RowText(Row); })
					.ColorAndOpacity_Lambda([this, Row]() { return RowColor(Row); })
				];
			}
			// Read-only and full-screen above every menu: it must never take a click or a hover (menumouse).
			SetVisibility(EVisibility::HitTestInvisible);
			ChildSlot
			.HAlign(HAlign_Left).VAlign(VAlign_Top)
			.Padding(TAttribute<FMargin>::CreateLambda([]()
			{
				FVector2D Size = FVector2D::ZeroVector;
				if (GEngine && GEngine->GameViewport)
				{
					GEngine->GameViewport->GetViewportSize(Size);
				}
				const FVector2D Origin = UmbrellaSoundLabel::ViewOrigin(Size);
				return FMargin(Origin.X + UmbrellaSoundLabel::ScreenPaddingPixels, Origin.Y + UmbrellaSoundLabel::ScreenPaddingPixels, 0.0f, 0.0f);
			}))
			[
				Rows
			];
		}

	private:
		FText RowText(int32 Row) const
		{
			const TArray<FUmbrellaSoundLabel> Labels = Board->GetVisibleLabels();
			return Labels.IsValidIndex(Row) ? FText::FromString(FUmbrellaSoundLabelBoard::FormatScreenLine(Labels[Row])) : FText::GetEmpty();
		}

		FSlateColor RowColor(int32 Row) const
		{
			const TArray<FUmbrellaSoundLabel> Labels = Board->GetVisibleLabels();
			const float Opacity = Labels.IsValidIndex(Row) ? FUmbrellaSoundLabelBoard::OpacityForAge(Labels[Row].Age) : 0.0f;
			return FSlateColor(FLinearColor(1.0f, 1.0f, 1.0f, Opacity));
		}

		TSharedPtr<FUmbrellaSoundLabelBoard> Board;
	};
}

FUmbrellaSoundLabelHud::FUmbrellaSoundLabelHud(TSharedRef<FUmbrellaSoundLabelBoard> InBoard)
	: Board(InBoard)
{
}

FUmbrellaSoundLabelHud::~FUmbrellaSoundLabelHud()
{
	Detach();
}

FKey FUmbrellaSoundLabelHud::GetToggleKey()
{
	return EKeys::F9;
}

void FUmbrellaSoundLabelHud::Arm(UWorld* World)
{
	if (bArmed)
	{
		return;
	}
	bArmed = true;
	AttachedWorld = World;
	TickHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([WeakHud = TWeakPtr<FUmbrellaSoundLabelHud>(AsShared())](float DeltaSeconds)
	{
		const TSharedPtr<FUmbrellaSoundLabelHud> Hud = WeakHud.Pin();
		if (Hud.IsValid())
		{
			Hud->OnFrame(DeltaSeconds);
		}
		return Hud.IsValid();
	}));
}

void FUmbrellaSoundLabelHud::OnFrame(float DeltaSeconds)
{
	UWorld* World = AttachedWorld.Get();
	if (World == nullptr || !World->IsPaused())
	{
		Board->Advance(DeltaSeconds);
	}
	if (!bConnected && AttachedWorld.IsValid())
	{
		Connect(AttachedWorld.Get());
	}
}

void FUmbrellaSoundLabelHud::Connect(UWorld* World)
{
	if (bConnected)
	{
		return;
	}
	APlayerController* Controller = World ? World->GetFirstPlayerController() : nullptr;
	ULocalPlayer* Local = Controller ? Controller->GetLocalPlayer() : nullptr;
	UEnhancedInputLocalPlayerSubsystem* InputSubsystem = Local ? Local->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>() : nullptr;
	if (InputSubsystem == nullptr)
	{
		return;
	}
	UInputAction* Action = NewObject<UInputAction>(GetTransientPackage(), TEXT("IA_SoundLabelToggle"));
	Action->ValueType = EInputActionValueType::Boolean;
	Action->bConsumeInput = false;
	Action->Triggers.Add(NewObject<UInputTriggerPressed>(Action));
	ToggleAction.Reset(Action);
	UInputMappingContext* Mapping = NewObject<UInputMappingContext>(GetTransientPackage(), TEXT("IMC_SoundLabel"));
	Mapping->MapKey(Action, GetToggleKey());
	Context.Reset(Mapping);
	InputSubsystem->AddMappingContext(Mapping, UmbrellaSoundLabel::ContextPriority);

	UEnhancedInputComponent* Input = NewObject<UEnhancedInputComponent>(Controller, TEXT("SoundLabelInput"));
	Input->RegisterComponent();
	const TSharedRef<FUmbrellaSoundLabelBoard> BoardRef = Board;
	Input->BindActionInstanceLambda(Action, ETriggerEvent::Triggered, [BoardRef](const FInputActionInstance&) { BoardRef->Toggle(); });
	Controller->PushInputComponent(Input);
	InputComponent.Reset(Input);

	if (GEngine && GEngine->GameViewport)
	{
		ListWidget = SNew(SSoundLabelList).Board(Board);
		GEngine->GameViewport->AddViewportWidgetContent(ListWidget.ToSharedRef(), UmbrellaSoundLabel::ViewportZOrder);
	}
	AttachedWorld = World;
	bConnected = true;
}

void FUmbrellaSoundLabelHud::Detach()
{
	if (bArmed)
	{
		FTSTicker::GetCoreTicker().RemoveTicker(TickHandle);
		bArmed = false;
	}
	if (!bConnected)
	{
		return;
	}
	bConnected = false;
	if (ListWidget.IsValid() && GEngine && GEngine->GameViewport)
	{
		GEngine->GameViewport->RemoveViewportWidgetContent(ListWidget.ToSharedRef());
	}
	ListWidget.Reset();
	APlayerController* Controller = AttachedWorld.IsValid() ? AttachedWorld->GetFirstPlayerController() : nullptr;
	if (Controller)
	{
		if (InputComponent.IsValid())
		{
			Controller->PopInputComponent(InputComponent.Get());
		}
		ULocalPlayer* Local = Controller->GetLocalPlayer();
		if (UEnhancedInputLocalPlayerSubsystem* InputSubsystem = Local ? Local->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>() : nullptr)
		{
			if (Context.IsValid())
			{
				InputSubsystem->RemoveMappingContext(Context.Get());
			}
		}
	}
	InputComponent.Reset();
	Context.Reset();
	ToggleAction.Reset();
}

#endif // UMBRELLAELLA_WORKBENCH

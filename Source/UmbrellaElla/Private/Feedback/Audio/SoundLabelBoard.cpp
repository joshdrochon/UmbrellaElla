#include "Feedback/Audio/SoundLabelBoard.h"

#if UMBRELLAELLA_WORKBENCH

#include "Core/UmbrellaLog.h"

FString FUmbrellaSoundLabelBoard::FormatLogLine(FName Id, const FString& Event, int32 Take)
{
	return FString::Printf(TEXT("SOUND_LABEL id=%s event=%s take=%02d"), *Id.ToString(), *Event, Take);
}

FString FUmbrellaSoundLabelBoard::FormatScreenLine(const FUmbrellaSoundLabel& Label)
{
	return FString::Printf(TEXT("%s | %s | take %02d"), *Label.Id.ToString(), *Label.Event, Label.Take);
}

int32 FUmbrellaSoundLabelBoard::TakeFromAssetName(const FString& AssetName)
{
	int32 Underscore = INDEX_NONE;
	if (!AssetName.FindLastChar(TEXT('_'), Underscore))
	{
		return 0;
	}
	const FString Suffix = AssetName.Mid(Underscore + 1);
	return Suffix.IsNumeric() ? FCString::Atoi(*Suffix) : 0;
}

float FUmbrellaSoundLabelBoard::OpacityForAge(float Age)
{
	return FMath::Clamp((UmbrellaSoundLabel::LineLifetimeSeconds - Age) / UmbrellaSoundLabel::LineFadeSeconds, 0.0f, 1.0f);
}

void FUmbrellaSoundLabelBoard::Note(FName Id, const FString& Event, int32 Take)
{
	FUmbrellaSoundLabel Label;
	Label.Id = Id;
	Label.Event = Event;
	Label.Take = Take;
	Labels.Add(Label);
	while (Labels.Num() > UmbrellaSoundLabel::MaxLines)
	{
		Labels.RemoveAt(0);
	}
	LastLogLine = FormatLogLine(Id, Event, Take);
	UE_LOG(LogUmbrellaElla, Display, TEXT("%s"), *LastLogLine);
}

void FUmbrellaSoundLabelBoard::Advance(float DeltaSeconds)
{
	for (FUmbrellaSoundLabel& Label : Labels)
	{
		Label.Age += DeltaSeconds;
	}
	Labels.RemoveAll([](const FUmbrellaSoundLabel& Label) { return Label.Age >= UmbrellaSoundLabel::LineLifetimeSeconds; });
}

TArray<FUmbrellaSoundLabel> FUmbrellaSoundLabelBoard::GetVisibleLabels() const
{
	return bShown ? Labels : TArray<FUmbrellaSoundLabel>();
}

#endif // UMBRELLAELLA_WORKBENCH

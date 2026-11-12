#include "Story/FlowStoryText.h"

TArray<FText> FFlowStoryText::GetEndingPages()
{
	TArray<FText> Pages;
	Pages.Add(FText::FromString(TEXT("Eventually, the owl's pursuit ends, and he retreats into the darkness, leaving Ella alive but still suspended between worlds.")));
	Pages.Add(FText::FromString(TEXT("She has survived, yet neither her fate nor the owl's intentions are resolved. Perhaps the owl has merely postponed his judgment, or perhaps something about Ella has challenged even his understanding of time.")));
	return Pages;
}

TArray<FText> FFlowStoryText::GetCreditsLines()
{
	TArray<FText> Lines;
	Lines.Add(FText::FromString(TEXT("Umbrella Ella")));
	Lines.Add(FText::FromString(TEXT("Rick Rispoli")));
	Lines.Add(FText::FromString(TEXT("Richard - Producer")));
	Lines.Add(FText::FromString(TEXT("Josh Rochon - Technical Lead")));
	return Lines;
}

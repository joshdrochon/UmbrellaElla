#include "Smoke/AgentPlayRules.h"

namespace
{
	struct FAgentPlayKeyAlias
	{
		const TCHAR* Word;
		const TCHAR* Engine;
	};

	// Default controls only (GDD SH1.0 section 3; UmbrellaInputBindings keyboard + mouse). No console, no function keys.
	const FAgentPlayKeyAlias AgentPlayKeys[] = {
		{TEXT("j"), TEXT("J")}, {TEXT("k"), TEXT("K")}, {TEXT("q"), TEXT("Q")}, {TEXT("e"), TEXT("E")},
		{TEXT("w"), TEXT("W")}, {TEXT("a"), TEXT("A")}, {TEXT("s"), TEXT("S")}, {TEXT("d"), TEXT("D")},
		{TEXT("space"), TEXT("SpaceBar")}, {TEXT("spacebar"), TEXT("SpaceBar")},
		{TEXT("shift"), TEXT("LeftShift")}, {TEXT("leftshift"), TEXT("LeftShift")},
		{TEXT("up"), TEXT("Up")}, {TEXT("down"), TEXT("Down")}, {TEXT("left"), TEXT("Left")}, {TEXT("right"), TEXT("Right")},
		{TEXT("1"), TEXT("One")}, {TEXT("2"), TEXT("Two")}, {TEXT("3"), TEXT("Three")}, {TEXT("4"), TEXT("Four")},
		{TEXT("["), TEXT("LeftBracket")}, {TEXT("]"), TEXT("RightBracket")},
		{TEXT("leftbracket"), TEXT("LeftBracket")}, {TEXT("rightbracket"), TEXT("RightBracket")},
		{TEXT("leftmouse"), TEXT("LeftMouseButton")}, {TEXT("leftmousebutton"), TEXT("LeftMouseButton")},
		{TEXT("rightmouse"), TEXT("RightMouseButton")}, {TEXT("rightmousebutton"), TEXT("RightMouseButton")},
	};

	bool AgentPlayParseMillis(const FString& Word, int32& Out)
	{
		if (Word.IsEmpty() || !Word.IsNumeric() || Word.Contains(TEXT(".")) || Word.Contains(TEXT("-")))
		{
			return false;
		}
		Out = FCString::Atoi(*Word);
		return true;
	}
}

FName AgentPlayRules::ResolveKeyName(const FString& Word)
{
	const FString Lower = Word.ToLower();
	for (const FAgentPlayKeyAlias& Alias : AgentPlayKeys)
	{
		if (Lower == Alias.Word)
		{
			return FName(Alias.Engine);
		}
	}
	return NAME_None;
}

AgentPlayRules::FTurn AgentPlayRules::ParseTurn(const FString& Text)
{
	FTurn Turn;
	TArray<FString> Lines;
	Text.ParseIntoArrayLines(Lines);
	int32 Cursor = 0;
	int32 End = 0;
	int32 Used = 0;
	for (const FString& Raw : Lines)
	{
		const FString Line = Raw.TrimStartAndEnd();
		if (Line.IsEmpty() || Line.StartsWith(TEXT("#")))
		{
			continue;
		}
		if (++Used > MaxLines)
		{
			Turn.Errors.Add(FString::Printf(TEXT("more than %d lines"), MaxLines));
			break;
		}
		TArray<FString> Words;
		Line.ParseIntoArrayWS(Words);
		const FString Verb = Words[0].ToLower();
		auto KeyOf = [&](int32 Index) { return Words.IsValidIndex(Index) ? ResolveKeyName(Words[Index]) : FName(NAME_None); };
		auto Add = [&](int32 At, FName Key, bool bPressed)
		{
			FKeyEvent Event;
			Event.Millis = At;
			Event.KeyName = Key;
			Event.bPressed = bPressed;
			Turn.Events.Add(Event);
			End = FMath::Max(End, At);
		};
		int32 Millis = 0;
		if (Verb == TEXT("wait"))
		{
			if (Words.Num() != 2 || !AgentPlayParseMillis(Words[1], Millis) || Millis > MaxTurnMillis)
			{
				Turn.Errors.Add(FString::Printf(TEXT("bad wait: %s"), *Line));
				continue;
			}
			Cursor += Millis;
			End = FMath::Max(End, Cursor);
		}
		else if (Verb == TEXT("release_all"))
		{
			Turn.bReleaseAllAtEnd = true;
		}
		else if (Verb == TEXT("down") || Verb == TEXT("up") || Verb == TEXT("tap") || Verb == TEXT("hold"))
		{
			const FName Key = KeyOf(1);
			if (Key.IsNone())
			{
				Turn.Errors.Add(FString::Printf(TEXT("not a default control: %s"), *Line));
				continue;
			}
			if (Verb == TEXT("down") || Verb == TEXT("up"))
			{
				if (Words.Num() != 2)
				{
					Turn.Errors.Add(FString::Printf(TEXT("bad line: %s"), *Line));
					continue;
				}
				Add(Cursor, Key, Verb == TEXT("down"));
			}
			else if (Verb == TEXT("tap"))
			{
				if (Words.Num() != 2)
				{
					Turn.Errors.Add(FString::Printf(TEXT("bad line: %s"), *Line));
					continue;
				}
				Add(Cursor, Key, true);
				Add(Cursor + TapMillis, Key, false);
			}
			else
			{
				if (Words.Num() != HoldWords || !AgentPlayParseMillis(Words[2], Millis) || Millis <= 0 || Millis > MaxTurnMillis)
				{
					Turn.Errors.Add(FString::Printf(TEXT("bad hold: %s"), *Line));
					continue;
				}
				Add(Cursor, Key, true);
				Add(Cursor + Millis, Key, false);
			}
		}
		else
		{
			Turn.Errors.Add(FString::Printf(TEXT("unknown command: %s"), *Line));
		}
	}
	if (End > MaxTurnMillis)
	{
		Turn.Errors.Add(FString::Printf(TEXT("turn longer than %d ms"), MaxTurnMillis));
	}
	// Time order; at the same instant a release comes before a press, so a key tapped twice in a row presses twice.
	Turn.Events.StableSort([](const FKeyEvent& A, const FKeyEvent& B)
	{
		return A.Millis != B.Millis ? A.Millis < B.Millis : (!A.bPressed && B.bPressed);
	});
	Turn.DurationMillis = FMath::Max(End, MinTurnMillis);
	return Turn;
}

float AgentPlayRules::IdleShare(float IdleSeconds, float Seconds)
{
	return Seconds > 0.0f ? FMath::Clamp(IdleSeconds / Seconds, 0.0f, 1.0f) : 1.0f;
}

FString AgentPlayRules::TurnFileName(int32 TurnNumber)
{
	return FString::Printf(TEXT("turn_%04d.txt"), TurnNumber);
}

FString AgentPlayRules::StopFileName()
{
	return TEXT("stop.txt");
}

FString AgentPlayRules::FrameFileName(int32 FrameNumber)
{
	return FString::Printf(TEXT("f%06d.jpg"), FrameNumber);
}

bool AgentPlayRules::IsFrameDue(double SinceLastFrameSeconds, double IntervalSeconds)
{
	return SinceLastFrameSeconds >= IntervalSeconds;
}

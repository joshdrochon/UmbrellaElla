#include "Feedback/Audio/UmbrellaCueTable.h"
#include "Feedback/Audio/UmbrellaCueData.h"

const TArray<FUmbrellaSoundCue>& UmbrellaCueTable::All()
{
	return UmbrellaCueData::Rows();
}

const TArray<FUmbrellaLoopGroupStop>& UmbrellaCueTable::GroupStops()
{
	return UmbrellaCueData::Stops();
}

FName UmbrellaCueTable::CueDetail(FName Detail)
{
	const FString Name = Detail.ToString();
	int32 Colons = INDEX_NONE;
	return Name.FindLastChar(TEXT(':'), Colons) && Colons > 0 && Name[Colons - 1] == TEXT(':') ? FName(*Name.Mid(Colons + 1)) : Detail;
}

bool UmbrellaCueTable::IsMatch(const FUmbrellaSoundCue& Cue, const FUmbrellaEvent& Event, FName PrevDetail)
{
	if (Cue.Event != Event.Type)
	{
		return false;
	}
	const FName Detail = CueDetail(Event.Detail);
	PrevDetail = CueDetail(PrevDetail);
	switch (Cue.Match)
	{
	case EUmbrellaCueMatch::Detail:
		return Detail == FName(Cue.Value);
	case EUmbrellaCueMatch::Target:
		return Event.TargetId == FName(Cue.Value);
	case EUmbrellaCueMatch::LeftDetail:
		return PrevDetail == FName(Cue.Value) && Detail != PrevDetail;
	case EUmbrellaCueMatch::Any:
	default:
		return true;
	}
}

TArray<const FUmbrellaSoundCue*> UmbrellaCueTable::ForEvent(const FUmbrellaEvent& Event, FName PrevDetail)
{
	TArray<const FUmbrellaSoundCue*> Out;
	for (const FUmbrellaSoundCue& Cue : All())
	{
		if (IsMatch(Cue, Event, PrevDetail))
		{
			Out.Add(&Cue);
		}
	}
	return Out;
}

const FUmbrellaSoundCue* UmbrellaCueTable::Find(FName Id)
{
	for (const FUmbrellaSoundCue& Cue : All())
	{
		if (Id == FName(Cue.Id))
		{
			return &Cue;
		}
	}
	return nullptr;
}

TArray<EUmbrellaEventType> UmbrellaCueTable::ListenedEvents()
{
	TArray<EUmbrellaEventType> Out;
	for (const FUmbrellaSoundCue& Cue : All())
	{
		if (Cue.Event != EUmbrellaEventType::Count)
		{
			Out.AddUnique(Cue.Event);
		}
	}
	for (const FUmbrellaLoopGroupStop& Stop : GroupStops())
	{
		Out.AddUnique(Stop.Event);
	}
	return Out;
}

const TCHAR* UmbrellaCueTable::ClassAssetName(EUmbrellaCueClass Class)
{
	switch (Class)
	{
	case EUmbrellaCueClass::Telegraph: return TEXT("SCL_Telegraph");
	case EUmbrellaCueClass::Music: return TEXT("SCL_Music");
	case EUmbrellaCueClass::UI: return TEXT("SCL_UI");
	case EUmbrellaCueClass::SFX:
	default: return TEXT("SCL_SFX");
	}
}

#pragma once

#include "CoreMinimal.h"

/** Source ids the Encounter Director stamps on Keeper attacks (shots, damage, wind). Health and the Keeper both read these. */
namespace UmbrellaSourceIds
{
	inline FName GustBand() { static const FName Id(TEXT("GUST_Band")); return Id; }
	inline FName TalonRake() { static const FName Id(TEXT("TALON_Rake")); return Id; }
	inline FName MechFrontCast() { static const FName Id(TEXT("MECH_Front_Cast")); return Id; }
	inline FName MechMiddleCurve() { static const FName Id(TEXT("MECH_Middle_Curve")); return Id; }
	inline FName MechRearTwoStage() { static const FName Id(TEXT("MECH_Rear_TwoStage")); return Id; }
	inline FName RedFan() { static const FName Id(TEXT("RED_Fan")); return Id; }
	inline FName ClockDoubleBeat() { static const FName Id(TEXT("CLOCK_DoubleBeat")); return Id; }
	inline FName YellowPacket() { static const FName Id(TEXT("YELLOW_Packet")); return Id; }
}

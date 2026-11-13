#pragma once

#include "CoreMinimal.h"

/** True constants of the nine-slot route grammar. Chunk numbers per slot (0 ends a row). */
namespace LevelGrammar
{
	static constexpr int32 MaxOptions = 5;
	static constexpr int32 SlotChunks[9][MaxOptions] = {
		{1, 0, 0, 0, 0},
		{2, 0, 0, 0, 0},
		{3, 0, 0, 0, 0},
		{4, 0, 0, 0, 0},
		{5, 6, 0, 0, 0},
		{7, 8, 0, 0, 0},
		{9, 10, 0, 0, 0},
		{5, 6, 7, 8, 0},
		{11, 12, 0, 0, 0}};

	/** Layout-stream seed mix (Knuth multiplicative hash), attempt stride, and 31-bit mask. */
	static constexpr int64 SeedMultiplier = 2654435761LL;
	static constexpr int64 AttemptStride = 40503LL;
	static constexpr int64 SeedMask = 0x7fffffffLL;

	/** Seed fixture proposals (illustrative, not test passes): seed -> ordered variants, ";" between refuge groups. */
	static constexpr int32 FixtureCount = 3;
	static constexpr int64 FixtureSeeds[FixtureCount] = {1001LL, 1002LL, 1003LL};
	static constexpr const TCHAR* FixtureRoutes[FixtureCount] = {
		TEXT("01A,02A,03A;04A,05A,07A;09A,08A,11A"),
		TEXT("01B,02B,03A;04B,06A,08B;10A,05B,12B"),
		TEXT("01A,02B,03B;04A,06B,07B;09B,08A,12A")};
}

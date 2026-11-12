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
}

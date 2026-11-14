#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Arena/UmbrellaArena.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaTuning.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "Feedback/Anim/KeeperPresenterSubsystem.h"
#include "Feedback/Art/ArtSlot.h"
#include "Feedback/Art/FigureScale.h"
#include "Feedback/Art/FrameCompositionSubsystem.h"
#include "Level/LevelPlan.h"
#include "Owl/KeeperOfTime.h"
#include "Owl/KeeperPartComponent.h"
#include "Tests/Shared/UmbrellaTestWorld.h"

/**
 * D-new-character-scale (Josh, 13 Nov; Ella 2x on 14 Nov): Ella draws 2x and the Keeper 1.5x, the camera does not move. Screen shares are
 * the opaque figure (alpha >= 128 in the picture's first cell) over the view height, with the real camera margin.
 */
namespace
{
	constexpr EAutomationTestFlags FigureTestFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter;

	/** Ella's opaque figure: 2x her original size (Josh, 14 Nov; old 1x: about 8-9%, 1.5x: about 13%). */
	constexpr float EllaShareMin = 0.15f;
	constexpr float EllaShareMax = 0.23f;
	/** The Keeper's opaque figure: toward 45-50%; the 1.5x scale lands it here (old: about 25%). */
	constexpr float KeeperShareMin = 0.36f;
	constexpr float KeeperShareMax = 0.52f;
	constexpr uint8 FigureAlphaSolid = 128;

	/** The opaque part of a picture's first cell, as fractions of the cell (0,0 = top-left). False when it cannot be read. */
	struct FFigureSpan
	{
		float Left = 0.0f;
		float Right = 1.0f;
		float Top = 0.0f;
		float Bottom = 1.0f;
	};

	bool FigureOpaqueSpan(UTexture2D* Texture, const FArtSlotRow& Row, FFigureSpan& Out)
	{
#if WITH_EDITORONLY_DATA
		// UE 5.8.4 Engine/Classes/Engine/Texture.h: FTextureSource::GetFormat (line 423), GetSizeX (line 417),
		// GetMipData(TArray64<uint8>&, int32 MipIndex, IImageWrapperModule*) (line 332).
		if (!IsValid(Texture) || !Texture->Source.IsValid() || Texture->Source.GetFormat() != TSF_BGRA8)
		{
			return false;
		}
		TArray64<uint8> Data;
		if (!Texture->Source.GetMipData(Data, 0))
		{
			return false;
		}
		const int64 Width = Texture->Source.GetSizeX();
		const int64 Height = Texture->Source.GetSizeY();
		const int64 CellW = Width / FMath::Max(1, Row.Cols);
		const int64 CellH = Height / FMath::Max(1, Row.Rows);
		if (CellW <= 0 || CellH <= 0 || Data.Num() < Width * Height * 4)
		{
			return false;
		}
		int64 MinX = CellW, MaxX = -1, MinY = CellH, MaxY = -1;
		for (int64 Y = 0; Y < CellH; ++Y)
		{
			for (int64 X = 0; X < CellW; ++X)
			{
				if (Data[(Y * Width + X) * 4 + 3] >= FigureAlphaSolid)
				{
					MinX = FMath::Min(MinX, X);
					MaxX = FMath::Max(MaxX, X);
					MinY = FMath::Min(MinY, Y);
					MaxY = FMath::Max(MaxY, Y);
				}
			}
		}
		if (MaxX < 0)
		{
			return false;
		}
		Out.Left = static_cast<float>(MinX) / CellW;
		Out.Right = static_cast<float>(MaxX + 1) / CellW;
		Out.Top = static_cast<float>(MinY) / CellH;
		Out.Bottom = static_cast<float>(MaxY + 1) / CellH;
		return true;
#else
		return false;
#endif
	}

	/** World box (X min/max, Z min/max) of the opaque figure drawn by an art-slot mesh. */
	struct FFigureBox
	{
		float MinX = 0.0f;
		float MaxX = 0.0f;
		float MinZ = 0.0f;
		float MaxZ = 0.0f;
		float Height() const { return MaxZ - MinZ; }
	};

	FFigureBox FigureBoxOf(const UStaticMeshComponent* Mesh, const FFigureSpan& Span)
	{
		const FVector Centre = Mesh->Bounds.Origin;
		const FVector Extent = Mesh->Bounds.BoxExtent;
		const float Left = static_cast<float>(Centre.X - Extent.X);
		const float Top = static_cast<float>(Centre.Z + Extent.Z);
		const float W = static_cast<float>(2.0 * Extent.X);
		const float H = static_cast<float>(2.0 * Extent.Z);
		FFigureBox Box;
		Box.MinX = Left + Span.Left * W;
		Box.MaxX = Left + Span.Right * W;
		Box.MaxZ = Top - Span.Top * H;
		Box.MinZ = Top - Span.Bottom * H;
		return Box;
	}

	struct FFrameView
	{
		float MinX = 0.0f;
		float MaxX = 0.0f;
		float MinZ = 0.0f;
		float MaxZ = 0.0f;
		float Height() const { return MaxZ - MinZ; }
	};

	FFrameView FrameViewOf(const UCameraComponent* Camera)
	{
		const FVector At = Camera->GetComponentLocation();
		const float HalfW = Camera->OrthoWidth * 0.5f;
		const float HalfH = HalfW / Camera->AspectRatio;
		return FFrameView{ static_cast<float>(At.X) - HalfW, static_cast<float>(At.X) + HalfW, static_cast<float>(At.Z) - HalfH, static_cast<float>(At.Z) + HalfH };
	}

	bool FigureInside(const FFigureBox& Box, const FFrameView& View)
	{
		return Box.MinX >= View.MinX && Box.MaxX <= View.MaxX && Box.MinZ >= View.MinZ && Box.MaxZ <= View.MaxZ;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFigureScaleRules, "UmbrellaElla.Feedback.FigureScale.VisualOnly", FigureTestFlags)

bool FFigureScaleRules::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("Ella draws 2x"), UmbrellaFigureScale::Ella, 2.0);
	TestEqual(TEXT("the Keeper draws 1.5x"), UmbrellaFigureScale::Keeper, 1.5);
	TestEqual(TEXT("Ella's drawn cell is the framed cell times her scale"), UmbrellaPresenterConst::ArtCellHeight, UmbrellaPresenterConst::FramedCellHeight * UmbrellaFigureScale::Ella);
	// No camera zoom: the margin frames the old cell height (2.7), not the drawn one.
	TestEqual(TEXT("camera frames the old cell"), UFrameCompositionSubsystem::SpriteHalfHeight(0.5f), static_cast<float>(2.7 * 100.0 * 0.5 * 0.5), 1.0e-3f);
	TestEqual(TEXT("Keeper body box is 1.5x the old 6.0"), UmbrellaKeeperPresenterConst::StandInScale.X, 6.0 * 1.5, 1.0e-6);
	// Ceiling clamp: the picture drops only by what would pass the limit, never rises.
	TestEqual(TEXT("figure under the limit is not moved"), UEllaAnimPresenterComponent::FigureDrop(900.0f, 100.0f, 1100.0f), 0.0f);
	TestEqual(TEXT("figure 22 over the limit drops 22"), UEllaAnimPresenterComponent::FigureDrop(1000.0f, 122.0f, 1100.0f), 22.0f);
	TestEqual(TEXT("clear top without a band is the frame top"), UFrameCompositionSubsystem::ClearTopZ(0.0f, 1600.0f, 16.0f / 9.0f, 0.0f), 450.0f, 1.0e-3f);
	TestEqual(TEXT("clear top with the title band"), UFrameCompositionSubsystem::ClearTopZ(0.0f, 1600.0f, 16.0f / 9.0f, 0.05f), 405.0f, 1.0e-3f);
	// Gameplay numbers do not follow the art.
	const FKeeperTuning& K = GetDefault<UUmbrellaTuning>()->Keeper;
	TestEqual(TEXT("clock hitbox unchanged"), K.ClockHalfExtent, FVector2D(70.0f, 70.0f));
	TestEqual(TEXT("wings hitbox unchanged"), K.WingsHalfExtent, FVector2D(180.0f, 110.0f));
	TestEqual(TEXT("Ella actor scale unchanged"), GetDefault<UUmbrellaTuning>()->Motor.ActorScaleAtReference, 0.5f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFigureScaleWorld, "UmbrellaElla.Feedback.World.FigureScaleOnScreen", FigureTestFlags)

bool FFigureScaleWorld::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	UWorld* World = Test.GetWorld();
	UFrameCompositionSubsystem* Frame = World ? World->GetSubsystem<UFrameCompositionSubsystem>() : nullptr;
	UEncounterDirectorSubsystem* Encounter = World ? World->GetSubsystem<UEncounterDirectorSubsystem>() : nullptr;
	AUmbrellaArena* Arena = World ? World->SpawnActor<AUmbrellaArena>(FVector::ZeroVector, FRotator::ZeroRotator) : nullptr;
	AEllaCharacter* Ella = Arena ? Test.SpawnElla(Arena->GetPlayerStartLocation()) : nullptr;
	if (!TestNotNull(TEXT("frame"), Frame) || !TestNotNull(TEXT("encounter"), Encounter) || !TestNotNull(TEXT("arena"), Arena)
		|| !TestNotNull(TEXT("ella"), Ella) || !TestNotNull(TEXT("camera"), Arena->GetPlayCamera()))
	{
		return false;
	}
	UCameraComponent* Camera = Arena->GetPlayCamera();
	UStaticMeshComponent* EllaMesh = FindObjectFast<UStaticMeshComponent>(Ella, FName(TEXT("EllaStandIn")));
	UEllaAnimPresenterComponent* EllaPresenter = Ella->FindComponentByClass<UEllaAnimPresenterComponent>();
	if (!TestNotNull(TEXT("Ella's presenter"), EllaPresenter))
	{
		return false;
	}
	const FArtSlotRow* EllaRow = ArtSlot::Find(TEXT("ella-state:Idle"));
	if (!TestNotNull(TEXT("Ella's picture"), EllaMesh) || !TestNotNull(TEXT("Ella row"), EllaRow) || !TestTrue(TEXT("Ella draws art"), ArtSlot::HasArt(EllaMesh)))
	{
		return false;
	}
	FFigureSpan EllaSpan;
	if (!FigureOpaqueSpan(ArtSlot::LoadTexture(*EllaRow), *EllaRow, EllaSpan))
	{
		AddWarning(TEXT("Ella's picture source is not readable BGRA8: the whole cell counts as her figure (stricter in-frame, looser share)"));
	}
	const float CapsuleHalf = Ella->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	const float CapsuleRadius = Ella->GetCapsuleComponent()->GetScaledCapsuleRadius();

	// Ella in Start Game (arena at the origin) and in the Director's Cut fight (title band shown), at the ceiling and the floor.
	struct FEllaCase { const TCHAR* Name; bool bKeeperArena; EFrameTitleBand Band; };
	const FEllaCase Cases[] = { { TEXT("Start Game"), false, EFrameTitleBand::None }, { TEXT("Director's Cut"), true, EFrameTitleBand::Shown } };
	for (const FEllaCase& Case : Cases)
	{
		Arena->MovePlayArea(Case.bKeeperArena ? LevelPlan::KeeperArenaOrigin() : FVector::ZeroVector);
		Frame->ApplyCameraMargin(Arena, Ella, Case.Band);
		const FFrameView View = FrameViewOf(Camera);
		const float Ceiling = static_cast<float>(Arena->LocalPoint(0.0f, 1.0f).Z) - CapsuleHalf;
		const float Floor = static_cast<float>(Arena->LocalPoint(0.0f, 0.0f).Z) + CapsuleHalf;
		const float MidX = static_cast<float>(Arena->LocalPoint(0.5f, 0.5f).X);
		for (const float Z : { Ceiling, Floor })
		{
			Ella->SetActorLocation(FVector(MidX, Ella->GetActorLocation().Y, Z));
			EllaPresenter->KeepFigureInFrame();
			EllaMesh->UpdateBounds();
			const FFigureBox Box = FigureBoxOf(EllaMesh, EllaSpan);
			const float Share = Box.Height() / View.Height();
			const TCHAR* Where = Z == Ceiling ? TEXT("ceiling") : TEXT("floor");
			AddInfo(FString::Printf(TEXT("%s, Ella at the %s: figure %.0f of view %.0f = %.1f%% of the screen height, figure z %.0f..%.0f, frame z %.0f..%.0f"),
				Case.Name, Where, Box.Height(), View.Height(), 100.0f * Share, Box.MinZ, Box.MaxZ, View.MinZ, View.MaxZ));
			TestTrue(FString::Printf(TEXT("%s: Ella's share %.3f in [%.2f, %.2f]"), Case.Name, Share, EllaShareMin, EllaShareMax), Share >= EllaShareMin && Share <= EllaShareMax);
			// B7/B11 (standing rule): her full figure stays in frame in Start Game and Director's Cut, at the ceiling too, and
			// in Director's Cut below the title band. The camera is unchanged (it frames the old cell); the picture is lowered.
			const float ClearTop = UFrameCompositionSubsystem::ClearTopZ(static_cast<float>(Camera->GetComponentLocation().Z), Camera->OrthoWidth, Camera->AspectRatio,
				Case.Band == EFrameTitleBand::Shown ? UmbrellaFrameConst::TitleBandShare : 0.0f);
			AddInfo(FString::Printf(TEXT("%s, Ella at the %s: picture lowered %.0f units to stay in frame"), Case.Name, Where, EllaPresenter->GetFigureDrop()));
			TestTrue(FString::Printf(TEXT("%s, Ella at the %s: fully in frame (figure top %.0f, clear top %.0f)"), Case.Name, Where, Box.MaxZ, ClearTop),
				FigureInside(Box, View) && Box.MaxZ <= ClearTop + 0.5f);
			// Art vs hitbox: her hurtbox stays inside the drawn figure (a graze on the art edge never hurts).
			const FVector At = Ella->GetActorLocation();
			TestTrue(FString::Printf(TEXT("%s: Ella's hurtbox inside her figure"), Case.Name),
				At.X - CapsuleRadius >= Box.MinX && At.X + CapsuleRadius <= Box.MaxX && At.Z - CapsuleHalf >= Box.MinZ && At.Z + CapsuleHalf <= Box.MaxZ);
			AddInfo(FString::Printf(TEXT("%s: Ella hurtbox height / figure height = %.2f (feel.json player ratio 0.6)"), Case.Name, 2.0f * CapsuleHalf / Box.Height()));
		}
	}

	// The Keeper at its fight anchor in the Director's Cut arena.
	Arena->MovePlayArea(LevelPlan::KeeperArenaOrigin());
	Encounter->SetManualStepping(true);
	Encounter->BeginKeeperFight();
	AKeeperOfTime* Keeper = Encounter->GetKeeper();
	if (!TestNotNull(TEXT("keeper"), Keeper))
	{
		return false;
	}
	if (UKeeperPresenterSubsystem* Presenter = World->GetSubsystem<UKeeperPresenterSubsystem>())
	{
		Presenter->ShowStandIn(Keeper);
	}
	UStaticMeshComponent* Body = FindObjectFast<UStaticMeshComponent>(Keeper, FName(TEXT("KeeperStandIn")));
	const FArtSlotRow* BodyRow = ArtSlot::Find(TEXT("keeper:body-hover-flap"));
	if (!TestNotNull(TEXT("Keeper body picture"), Body) || !TestNotNull(TEXT("Keeper row"), BodyRow) || !TestTrue(TEXT("Keeper draws art"), ArtSlot::HasArt(Body)))
	{
		return false;
	}
	FFigureSpan KeeperSpan;
	if (!FigureOpaqueSpan(ArtSlot::LoadTexture(*BodyRow), *BodyRow, KeeperSpan))
	{
		AddWarning(TEXT("Keeper body picture source is not readable BGRA8: the whole cell counts as its figure"));
	}
	Ella->SetActorLocation(Arena->GetPlayerStartLocation());
	Frame->ApplyCameraMargin(Arena, Ella, EFrameTitleBand::Shown);
	Body->UpdateBounds();
	const FFrameView View = FrameViewOf(Camera);
	const FFigureBox KeeperBox = FigureBoxOf(Body, KeeperSpan);
	const float KeeperShare = KeeperBox.Height() / View.Height();
	AddInfo(FString::Printf(TEXT("Keeper: figure %.0f x %.0f of view %.0f x %.0f = %.1f%% of the screen height; figure x %.0f..%.0f z %.0f..%.0f, frame x %.0f..%.0f z %.0f..%.0f"),
		KeeperBox.MaxX - KeeperBox.MinX, KeeperBox.Height(), View.MaxX - View.MinX, View.Height(), 100.0f * KeeperShare,
		KeeperBox.MinX, KeeperBox.MaxX, KeeperBox.MinZ, KeeperBox.MaxZ, View.MinX, View.MaxX, View.MinZ, View.MaxZ));
	TestTrue(FString::Printf(TEXT("Keeper share %.3f in [%.2f, %.2f]"), KeeperShare, KeeperShareMin, KeeperShareMax), KeeperShare >= KeeperShareMin && KeeperShare <= KeeperShareMax);
	TestTrue(TEXT("Keeper fully in frame"), FigureInside(KeeperBox, View));

	// Art vs hitbox: every Keeper target sits on the drawn figure (a shot that looks like a hit can be one).
	const FKeeperTuning& K = GetDefault<UUmbrellaTuning>()->Keeper;
	struct FPartCase { EKeeperPart Part; const TCHAR* Name; FVector2D Half; };
	const FPartCase Parts[] = {
		{ EKeeperPart::Wings, TEXT("wings"), K.WingsHalfExtent }, { EKeeperPart::Clock, TEXT("clock"), K.ClockHalfExtent },
		{ EKeeperPart::Eye, TEXT("eye"), K.EyeHalfExtent }, { EKeeperPart::Front, TEXT("front mechanism"), K.MechanismHalfExtent },
		{ EKeeperPart::Middle, TEXT("middle mechanism"), K.MechanismHalfExtent }, { EKeeperPart::Rear, TEXT("rear mechanism"), K.MechanismHalfExtent },
	};
	const FVector Anchor = Keeper->GetActorLocation();
	for (const FPartCase& Part : Parts)
	{
		const UKeeperPartComponent* Hit = Keeper->GetPartComponent(Part.Part);
		if (!TestNotNull(Part.Name, Hit))
		{
			continue;
		}
		const FVector C = Hit->GetComponentLocation();
		TestTrue(FString::Printf(TEXT("%s hitbox lies on the drawn Keeper"), Part.Name),
			C.X - Part.Half.X >= KeeperBox.MinX && C.X + Part.Half.X <= KeeperBox.MaxX && C.Z - Part.Half.Y >= KeeperBox.MinZ && C.Z + Part.Half.Y <= KeeperBox.MaxZ);
		// Report (do not fix): the picture grew about the body centre, so a part drawn at offset O now draws at 1.5 O.
		const FVector2D Offset(C.X - Anchor.X, C.Z - Anchor.Z);
		const FVector2D Shift = Offset * static_cast<float>(UmbrellaFigureScale::Keeper - 1.0);
		const bool bStillOver = FMath::Abs(Shift.X) <= Part.Half.X && FMath::Abs(Shift.Y) <= Part.Half.Y;
		AddInfo(FString::Printf(TEXT("%s: hitbox offset (%.0f, %.0f) half (%.0f, %.0f); the 1.5x picture moves its drawn part by (%.0f, %.0f): %s"),
			Part.Name, Offset.X, Offset.Y, Part.Half.X, Part.Half.Y, Shift.X, Shift.Y, bStillOver ? TEXT("drawn centre still over its hitbox") : TEXT("REPORT drawn centre leaves its hitbox")));
	}
	return true;
}

#endif

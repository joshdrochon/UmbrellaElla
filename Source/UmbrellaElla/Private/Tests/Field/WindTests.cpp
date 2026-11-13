#include "Engine/Engine.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/World.h"
#include "Field/WindCurrent.h"
#include "GameFramework/Pawn.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

namespace
{
	struct FWindProbe
	{
		int32 Entered = 0;
		int32 Exited = 0;
		FUmbrellaEvent Last;
		void OnEntered(const FUmbrellaEvent& Event) { ++Entered; Last = Event; }
		void OnExited(const FUmbrellaEvent& Event) { ++Exited; }
	};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWindDirectionLabel, "UmbrellaElla.Field.DirectionLabel",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FWindDirectionLabel::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("left"), AWindCurrent::DirectionLabel(FVector(-1.0, 0.0, 0.0)), FName(TEXT("Left")));
	TestEqual(TEXT("right"), AWindCurrent::DirectionLabel(FVector(1.0, 0.0, 0.2)), FName(TEXT("Right")));
	TestEqual(TEXT("up"), AWindCurrent::DirectionLabel(FVector(0.0, 0.0, 1.0)), FName(TEXT("Up")));
	TestEqual(TEXT("down"), AWindCurrent::DirectionLabel(FVector(0.1, 0.0, -1.0)), FName(TEXT("Down")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWindWorldEvents, "UmbrellaElla.Field.World.BroadcastsEnterExit",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FWindWorldEvents::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	AWindCurrent* Wind = World->SpawnActor<AWindCurrent>();
	APawn* Ella = World->SpawnActor<APawn>();
	UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World);
	bool bOk = TestNotNull(TEXT("wind"), Wind) && TestNotNull(TEXT("pawn"), Ella) && TestNotNull(TEXT("bus"), Bus);
	if (bOk)
	{
		Wind->SetCurrent(FVector(-1.0, 0.0, 0.0), 250.0f);
		const TSharedRef<FWindProbe> Probe = MakeShared<FWindProbe>();
		const FDelegateHandle In = Bus->On(EUmbrellaEventType::WindEntered).AddSP(Probe, &FWindProbe::OnEntered);
		const FDelegateHandle Out = Bus->On(EUmbrellaEventType::WindExited).AddSP(Probe, &FWindProbe::OnExited);
		Wind->BroadcastEntered(Ella);
		Wind->BroadcastExited(Ella);
		TestEqual(TEXT("entered once"), Probe->Entered, 1);
		TestEqual(TEXT("exited once"), Probe->Exited, 1);
		TestEqual(TEXT("force in Value"), Probe->Last.Value, 250.0f);
		TestEqual(TEXT("direction in Detail"), Probe->Last.Detail, FName(TEXT("Left")));
		TestEqual(TEXT("target is pawn"), Probe->Last.TargetId, Ella->GetFName());
		Bus->On(EUmbrellaEventType::WindEntered).Remove(In);
		Bus->On(EUmbrellaEventType::WindExited).Remove(Out);
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return bOk;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWindDrawnWidth, "UmbrellaElla.Field.World.DrawnWidthMatchesUsable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FWindDrawnWidth::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("right is transport"), AWindCurrent::KindFor(FVector(1, 0, 0), false), EWindKind::Transport);
	TestEqual(TEXT("down is descent"), AWindCurrent::KindFor(FVector(0, 0, -1), false), EWindKind::Descent);
	TestEqual(TEXT("up is rescue"), AWindCurrent::KindFor(FVector(0, 0, 1), false), EWindKind::Rescue);
	TestEqual(TEXT("local field is rescue"), AWindCurrent::KindFor(FVector(1, 0, 0), true), EWindKind::Rescue);
	TestNotEqual(TEXT("transport/descent tint differ"), AWindCurrent::KindTint(EWindKind::Transport), AWindCurrent::KindTint(EWindKind::Descent));
	TestNotEqual(TEXT("descent/rescue tint differ"), AWindCurrent::KindTint(EWindKind::Descent), AWindCurrent::KindTint(EWindKind::Rescue));

	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	struct FCase { FVector Dir; bool bLocal; float HalfX; float HalfZ; };
	const FCase Cases[] = { { FVector(1, 0, 0), false, 400.0f, 100.0f }, { FVector(0, 0, -1), false, 100.0f, 500.0f }, { FVector(1, 0, 0), true, 300.0f, 150.0f } };
	for (const FCase& Case : Cases)
	{
		AWindCurrent* Wind = World->SpawnActor<AWindCurrent>();
		if (!TestNotNull(TEXT("wind"), Wind))
		{
			continue;
		}
		Wind->SetHalfExtent(Case.HalfX, Case.HalfZ);
		Wind->SetCurrent(Case.Dir, 200.0f);
		if (Case.bLocal)
		{
			Wind->SetLocalVerticalField(1.0f, 0.0f, 0.0f);
		}
		TestTrue(TEXT("drawn"), Wind->IsDrawn());
		TestEqual(TEXT("usable width"), Wind->GetUsableSize().X, Case.HalfX * 2.0);
		TestEqual(TEXT("drawn width equals usable"), Wind->GetDrawnSize().X, Wind->GetUsableSize().X);
		TestEqual(TEXT("drawn height equals usable"), Wind->GetDrawnSize().Y, Wind->GetUsableSize().Y);
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

#endif

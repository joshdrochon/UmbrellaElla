#include "Engine/Engine.h"
#include "Core/EllaCharacter.h"
#include "Input/EllaInputAdapterComponent.h"
#include "Tests/Shared/UmbrellaTestWorld.h"
#include "Umbrella/UmbrellaPlayerIds.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/World.h"
#include "Field/WindCurrent.h"
#include "Components/StaticMeshComponent.h"
#include "Level/LevelContracts.h"
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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWindWorldMovesRealElla, "UmbrellaElla.Field.World.CurrentTargetsEllaAndMovesHer",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FWindWorldMovesRealElla::RunTest(const FString& Parameters)
{
	// WIND-03 regression: the real current's own broadcast must reach the real Motor (TargetId = the player id).
	FUmbrellaTestWorld Test;
	UWorld* World = Test.GetWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	const FVector Start(0.0, 0.0, 540.0);
	AEllaCharacter* Ella = Test.SpawnElla(Start);
	AWindCurrent* Wind = World->SpawnActor<AWindCurrent>(AWindCurrent::StaticClass(), FTransform(Start));
	UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World);
	if (!TestNotNull(TEXT("Ella"), Ella) || !TestNotNull(TEXT("wind"), Wind) || !TestNotNull(TEXT("bus"), Bus))
	{
		return false;
	}
	TestEqual(TEXT("Ella's target id is the player id"), AWindCurrent::TargetIdFor(Ella), UmbrellaPlayerIds::Ella);
	Wind->SetCurrent(FVector(1.0, 0.0, 0.0), 300.0f);
	const TSharedRef<FWindProbe> Probe = MakeShared<FWindProbe>();
	const FDelegateHandle In = Bus->On(EUmbrellaEventType::WindEntered).AddSP(Probe, &FWindProbe::OnEntered);
	Wind->BroadcastEntered(Ella);
	TestEqual(TEXT("broadcast names Ella by player id"), Probe->Last.TargetId, UmbrellaPlayerIds::Ella);
	Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Ride);
	const float Dt = 1.0f / 60.0f;
	for (int32 Frame = 0; Frame < 30; ++Frame)
	{
		Test.TickFrames(1, Dt);
		FVector Location = Ella->GetActorLocation();
		Location.Z = Start.Z;
		Ella->SetActorLocation(Location);
	}
	const double Moved = Ella->GetActorLocation().X - Start.X;
	TestTrue(FString::Printf(TEXT("the current carries Ella right (moved %.1f)"), Moved), Moved > 50.0);
	Wind->BroadcastExited(Ella);
	const double AtExit = Ella->GetActorLocation().X;
	Test.TickSeconds(2.0f, Dt);
	TestTrue(TEXT("leaving the current ends the push (decays, never reverses)"), Ella->GetActorLocation().X >= AtExit - 1.0);
	Bus->On(EUmbrellaEventType::WindEntered).Remove(In);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FWindWorldDrawsField, "UmbrellaElla.Field.World.CurrentDrawsItsUsableWidth",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FWindWorldDrawsField::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld TestWorld;
	UWorld* World = TestWorld.GetWorld();
	AWindCurrent* Wind = World ? World->SpawnActor<AWindCurrent>() : nullptr;
	if (!TestNotNull(TEXT("wind current"), Wind))
	{
		return false;
	}
	Wind->SetHalfExtent(100.0f, 150.0f);
	Wind->SetCurrent(FVector(1.0, 0.0, 0.0), 300.0f);
	const UStaticMeshComponent* Field = Wind->GetField();
	TestTrue(TEXT("field is drawn"), Field && Field->IsVisible() && Field->GetStaticMesh() != nullptr);
	TestEqual(TEXT("field never collides"), Field ? Field->GetCollisionEnabled() : ECollisionEnabled::QueryAndPhysics, ECollisionEnabled::NoCollision);
	TestEqual(TEXT("usable width"), Wind->GetUsableWidth(), 200.0f, 0.5f);
	TestEqual(TEXT("drawn width equals usable width"), Wind->GetDrawnWidth(), Wind->GetUsableWidth(), 0.5f);
	TestEqual(TEXT("drawn height equals usable height"), Field ? static_cast<float>(Field->Bounds.BoxExtent.Z) : 0.0f, 150.0f, 0.5f);
	TestTrue(TEXT("readability contract holds"), LevelContracts::IsWindFieldDrawnTrue(Wind->GetDrawnWidth(), Wind->GetUsableWidth(), 1.0f));
	TestTrue(TEXT("field is behind Ella"), Field && Field->GetComponentLocation().Y < Wind->GetActorLocation().Y);
	Wind->SetHalfExtent(40.0f, 150.0f);
	TestEqual(TEXT("a resized current redraws"), Wind->GetDrawnWidth(), 80.0f, 0.5f);
	// Transport, descent, lift (rescue) and return read differently.
	TestEqual(TEXT("right is transport"), AWindCurrent::RoleLabel(FVector(1.0, 0.0, 0.0)), FName(TEXT("Transport")));
	TestEqual(TEXT("down is descent"), AWindCurrent::RoleLabel(FVector(0.0, 0.0, -1.0)), FName(TEXT("Descent")));
	TestEqual(TEXT("up is lift"), AWindCurrent::RoleLabel(FVector(0.0, 0.0, 1.0)), FName(TEXT("Lift")));
	TestEqual(TEXT("left is return"), AWindCurrent::RoleLabel(FVector(-1.0, 0.0, 0.0)), FName(TEXT("Return")));
	TSet<FLinearColor> Colours;
	for (const TCHAR* Role : {TEXT("Transport"), TEXT("Descent"), TEXT("Lift"), TEXT("Return")})
	{
		Colours.Add(AWindCurrent::FieldColourFor(FName(Role)));
	}
	TestEqual(TEXT("four distinct role colours"), Colours.Num(), 4);
	return true;
}

#endif

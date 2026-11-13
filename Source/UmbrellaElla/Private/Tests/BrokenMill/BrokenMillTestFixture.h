#pragma once

#if WITH_AUTOMATION_TESTS

#include "CoreMinimal.h"
#include "BrokenMill/BrokenMillRoom.h"
#include "BrokenMill/BrokenMillRules.h"
#include "BrokenMill/BrokenMillTuning.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Tests/Shared/UmbrellaTestWorld.h"
#include "Umbrella/UmbrellaPlayerIds.h"

#define UMBRELLAELLA_MILL_FLAGS (EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

/** Shared Broken Mill world-test fixtures (real Ella, real room, real winds). */
namespace BrokenMillTest
{
	/** Real Ella plus a built room at an offset; the room's target is Ella. */
	struct FMillIntegratedFixture
	{
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = nullptr;
		ABrokenMillRoom* Room = nullptr;

		/**
		 * bNamedElla spawns Ella with the actor name "Ella". The real AWindCurrent puts the pawn's actor name in
		 * TargetId and the Motor answers only to "Ella" (WIND-03, levelchunks lane); with this name the REAL overlap
		 * event reaches the Motor unchanged. Remove the name once WIND-03 is fixed on main.
		 */
		AEllaCharacter* Spawn(const FVector2D& EllaRoomPoint, bool bNamedElla = false)
		{
			UWorld* World = Test.GetWorld();
			if (!World)
			{
				return nullptr;
			}
			Room = World->SpawnActor<ABrokenMillRoom>(ABrokenMillRoom::StaticClass(), FTransform(FVector(10000.0, 0.0, 0.0)));
			if (!Room)
			{
				return nullptr;
			}
			Room->BuildRoom();
			if (bNamedElla)
			{
				FActorSpawnParameters Params;
				Params.Name = UmbrellaPlayerIds::Ella;
				Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
				Ella = World->SpawnActor<AEllaCharacter>(AEllaCharacter::StaticClass(), FTransform(Room->RoomToWorld(EllaRoomPoint)), Params);
			}
			else
			{
				Ella = Test.SpawnElla(Room->RoomToWorld(EllaRoomPoint));
			}
			if (Ella)
			{
				Room->SetTargetActor(Ella);
			}
			return Ella;
		}

		/** Tick with Ella's height pinned (a held trim), so only the Motor's sideways motion moves her. */
		void TickPinnedZ(float Seconds, float Dt)
		{
			const double Z = Ella->GetActorLocation().Z;
			for (int32 Frame = 0; Frame < FMath::RoundToInt(Seconds / Dt); ++Frame)
			{
				Test.TickFrames(1, Dt);
				FVector Location = Ella->GetActorLocation();
				Location.Z = Z;
				Ella->SetActorLocation(Location);
			}
		}

		int32 CountShots() const { return Test.CountActors<AUmbrellaProjectile>(); }
		FVector2D EllaRoom() const { return Room->WorldToRoom(Ella->GetActorLocation()); }

		/** Tick until Ella's root falls to Z (or the time runs out); returns the seconds it took. */
		float TickUntilRootBelow(float Z, float MaxSeconds, float Dt)
		{
			float Elapsed = 0.0f;
			while (EllaRoom().Y > Z && Elapsed < MaxSeconds)
			{
				Test.TickFrames(1, Dt);
				Elapsed += Dt;
			}
			return Elapsed;
		}
	};

	/** What the bus said about Ella: wind enter/exit by source (TargetId = Ella's name) and shot contacts on her. */
	struct FMillEllaEventState
	{
		TArray<FName> Entered;
		TArray<FName> Exited;
		TMap<FName, bool> Inside;
		int32 ShotContactsOnElla = 0;
		FName EllaName;
	};

	/** Subscribes on Attach and unsubscribes when it goes away; the handlers share the state, never 'this'. */
	struct FMillEllaEventLog
	{
		TSharedRef<FMillEllaEventState> State = MakeShared<FMillEllaEventState>();
		UUmbrellaEventBus* Bus = nullptr;
		FDelegateHandle EnteredHandle;
		FDelegateHandle ExitedHandle;
		FDelegateHandle ContactHandle;

		void Attach(UWorld* World, FName InEllaName)
		{
			State->EllaName = InEllaName;
			Bus = UUmbrellaEventBus::Get(World);
			if (!Bus)
			{
				return;
			}
			TSharedRef<FMillEllaEventState> Shared = State;
			EnteredHandle = Bus->On(EUmbrellaEventType::WindEntered).AddLambda([Shared](const FUmbrellaEvent& Event)
			{
				if (Event.TargetId == Shared->EllaName)
				{
					Shared->Entered.Add(Event.SourceId);
					Shared->Inside.Add(Event.SourceId, true);
				}
			});
			ExitedHandle = Bus->On(EUmbrellaEventType::WindExited).AddLambda([Shared](const FUmbrellaEvent& Event)
			{
				if (Event.TargetId == Shared->EllaName)
				{
					Shared->Exited.Add(Event.SourceId);
					Shared->Inside.Add(Event.SourceId, false);
				}
			});
			ContactHandle = Bus->On(EUmbrellaEventType::ProjectileContact).AddLambda([Shared](const FUmbrellaEvent& Event)
			{
				Shared->ShotContactsOnElla += Event.TargetId == Shared->EllaName ? 1 : 0;
			});
		}

		/** True when the last wind event for this source was an enter (an overlap at spawn may precede Attach). */
		bool IsInside(FName Source) const { return State->Inside.FindRef(Source); }

		int32 ShotContactsOnElla() const { return State->ShotContactsOnElla; }

		~FMillEllaEventLog()
		{
			if (Bus)
			{
				Bus->On(EUmbrellaEventType::WindEntered).Remove(EnteredHandle);
				Bus->On(EUmbrellaEventType::WindExited).Remove(ExitedHandle);
				Bus->On(EUmbrellaEventType::ProjectileContact).Remove(ContactHandle);
			}
		}
	};

	/** Put the Motor at a lift multiplier through the real health event (Value = active hits, Amount = capacity). */
	inline void MillSetLiftByHealth(UWorld* World, float ActiveHits, int32 CapacityHits)
	{
		if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World))
		{
			FUmbrellaEvent Event;
			Event.Type = EUmbrellaEventType::PlayerHealthChanged;
			Event.SourceId = UmbrellaPlayerIds::Ella;
			Event.Value = ActiveHits;
			Event.Amount = CapacityHits;
			Bus->Broadcast(Event);
		}
	}
	/** Pin Ella's whole root (X and Z) while the world ticks: a measurement stand, not a Motor path. */
	inline void MillTickPinned(FMillIntegratedFixture& F, const FVector2D& RoomPoint, int32 Frames, float Dt)
	{
		for (int32 Frame = 0; Frame < Frames; ++Frame)
		{
			F.Ella->SetActorLocation(F.Room->RoomToWorld(RoomPoint));
			F.Test.TickFrames(1, Dt);
		}
		F.Ella->SetActorLocation(F.Room->RoomToWorld(RoomPoint));
	}

	/**
	 * Every real projectile in the world, seen frame by frame: where and when it left, Ella's root at that frame,
	 * its path (lowest distance to a point of interest), where it ended and whether the guard consumed it.
	 */
	struct FMillShotTrack
	{
		TWeakObjectPtr<AUmbrellaProjectile> Shot;
		EUmbrellaShotKind Kind = EUmbrellaShotKind::PlayerBlast;
		FVector2D Origin = FVector2D::ZeroVector;
		FVector2D RootAtEmission = FVector2D::ZeroVector;
		FVector2D RootBeforeEmission = FVector2D::ZeroVector;
		FVector2D Last = FVector2D::ZeroVector;
		float Radius = 0.0f;
		float Speed = 0.0f;
		float Damage = 0.0f;
		float Lifetime = 0.0f;
		float EmitTime = 0.0f;
		float EndTime = -1.0f;
		float MinDistanceToPoint = TNumericLimits<float>::Max();
		float MinX = TNumericLimits<float>::Max();
		bool bHitGuard = false;
	};

	struct FMillShotTracker
	{
		TArray<FMillShotTrack> Tracks;
		FVector2D PointOfInterest = FVector2D::ZeroVector;
		float Clock = 0.0f;
		FVector2D RootBefore = FVector2D::ZeroVector;

		/** Call before a tick: remembers Ella's root at the start of the frame. */
		void BeginFrame(const FMillIntegratedFixture& F) { RootBefore = F.EllaRoom(); }

		/** Call after a tick with the guard HP from before it. */
		void EndFrame(const FMillIntegratedFixture& F, float Dt, float GuardHpBefore)
		{
			Clock += Dt;
			UWorld* World = F.Test.GetWorld();
			TSet<AUmbrellaProjectile*> Known;
			for (const FMillShotTrack& Track : Tracks)
			{
				if (Track.Shot.IsValid())
				{
					Known.Add(Track.Shot.Get());
				}
			}
			for (TActorIterator<AUmbrellaProjectile> It(World); It; ++It)
			{
				if (Known.Contains(*It) || It->IsActorBeingDestroyed())
				{
					continue;
				}
				FMillShotTrack& Track = Tracks.AddDefaulted_GetRef();
				const FUmbrellaShotSpec& Spec = It->GetSpec();
				Track.Shot = *It;
				Track.Kind = Spec.Kind;
				Track.Origin = F.Room->WorldToRoom(Spec.Origin);
				Track.RootAtEmission = F.EllaRoom();
				Track.RootBeforeEmission = RootBefore;
				Track.Radius = Spec.Radius;
				Track.Speed = Spec.Velocity.Size();
				Track.Damage = Spec.Damage;
				Track.Lifetime = Spec.LifetimeSeconds;
				Track.EmitTime = Clock - Dt;
				Track.Last = Track.Origin;
				Track.MinDistanceToPoint = FVector2D::Distance(Track.Origin, PointOfInterest);
				Track.MinX = Track.Origin.X;
			}
			int32 Ended = 0;
			FMillShotTrack* EndedTrack = nullptr;
			for (FMillShotTrack& Track : Tracks)
			{
				if (Track.EndTime >= 0.0f)
				{
					continue;
				}
				if (Track.Shot.IsValid() && !Track.Shot->IsActorBeingDestroyed())
				{
					// Sample the straight segment since the last frame so the closest approach is not missed.
					const FVector2D Now = F.Room->WorldToRoom(Track.Shot->GetActorLocation());
					const FVector2D Edge = Now - Track.Last;
					const double Length2 = Edge.SizeSquared();
					const double Along = Length2 > 0.0 ? FMath::Clamp(FVector2D::DotProduct(PointOfInterest - Track.Last, Edge) / Length2, 0.0, 1.0) : 0.0;
					Track.MinDistanceToPoint = FMath::Min(Track.MinDistanceToPoint, static_cast<float>(FVector2D::Distance(PointOfInterest, Track.Last + Edge * Along)));
					Track.MinX = FMath::Min(Track.MinX, static_cast<float>(Now.X));
					Track.Last = Now;
					continue;
				}
				Track.EndTime = Clock;
				++Ended;
				EndedTrack = &Track;
			}
			// The guard loses HP only to a consumed player shot; at most one shot ends per frame at this cadence.
			if (F.Room->GetGuardHp() < GuardHpBefore && Ended == 1 && EndedTrack && EndedTrack->Kind == EUmbrellaShotKind::PlayerBlast)
			{
				EndedTrack->bHitGuard = true;
			}
		}

		/** Counting stand: a downed guard is restored at once (and kept disabled), so every hit is counted. */
		bool bReviveGuard = false;

		/** One tick with bookkeeping. */
		void Step(FMillIntegratedFixture& F, float Dt)
		{
			BeginFrame(F);
			const float Hp = F.Room->GetGuardHp();
			F.Test.TickFrames(1, Dt);
			EndFrame(F, Dt, Hp);
			if (bReviveGuard && F.Room->GetGuardHp() <= 0.0f)
			{
				F.Room->ResetForRestart();
				F.Room->DisableGuard();
			}
		}

		int32 CountKind(EUmbrellaShotKind Kind) const
		{
			int32 Count = 0;
			for (const FMillShotTrack& Track : Tracks)
			{
				Count += Track.Kind == Kind ? 1 : 0;
			}
			return Count;
		}

		int32 CountGuardHits() const
		{
			int32 Count = 0;
			for (const FMillShotTrack& Track : Tracks)
			{
				Count += Track.bHitGuard ? 1 : 0;
			}
			return Count;
		}

		bool HasAllEnded() const
		{
			for (const FMillShotTrack& Track : Tracks)
			{
				if (Track.EndTime < 0.0f)
				{
					return false;
				}
			}
			return true;
		}
	};
}

#endif

import math
import pygame

def seek(entity_rect, target_rect, speed, dt):

    dx = target_rect.centerx - entity_rect.centerx
    dy = target_rect.centery - entity_rect.centery
    dist = max(math.hypot(dx, dy), 1)
    return (dx / dist) * speed * dt, (dy / dist) * speed * dt

def separate(entity, neighbors, radius, strength):

    push_x, push_y = 0.0, 0.0
    for n in neighbors:
        if n is entity:
            continue
        dx = entity.rect.centerx - n.rect.centerx
        dy = entity.rect.centery - n.rect.centery
        dist = max(math.hypot(dx, dy), 1)
        if dist < radius and dist > 0:
            # closer = stronger push
            force = (radius - dist) / radius * strength
            push_x += (dx / dist) * force
            push_y += (dy / dist) * force
    return push_x, push_y

def avoid_obstacles(entity_rect, obstacles, look_ahead, facing_dx, facing_dy):

    # check a rect projected ahead in movement direction
    probe = entity_rect.move(
        round(facing_dx * look_ahead),
        round(facing_dy * look_ahead)
    )
    for obs in obstacles:
        if probe.colliderect(obs.hitbox):
            # perpendicular to movement direction
            return -facing_dy, facing_dx
    return 0.0, 0.0

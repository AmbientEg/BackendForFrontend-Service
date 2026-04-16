# 1 Buildings
# POST   /admin/buildings
# GET    /admin/buildings/{id}


# 2 Floors
# POST   /admin/floors
# PUT    /admin/floors/{id}
# GET    /admin/floors/{id}/map


# 3 Graph Management
# POST /admin/graphs/rebuild/{buildingId}
# POST /admin/graphs/confirm/{buildingId}
# POST /admin/graphs/rollback/{buildingId}



# invalidate cache
# await route_cache.invalidate_building(building_id)


# These trigger:
# cache invalidation
# graph updates

# 4 POIs

# PUT    /admin/pois/{poiId}
# DELETE /admin/pois/{poiId}

# invalidate cache
# await route_cache.invalidate_building(building_id)

# 5 Validation
# All /admin/* endpoints:
# def require_admin(user):
#     if user.role != "admin":
#         raise HTTPException(403)
# Flow:
# Admin → BFF → JWT validation → forward to service

# ASH real-time strategy game

This was one of the projects I made over the first Covid lockdown, when I was 16. I made it using Pygame and assets I created myself using microsoft paint. It is exclusively coded in python.

It isn't quite finished, but I have most of the game in place: pathfinding (A*), resource collection, random map generation, building, unit creation (with queues), start and pause menus, tooltip window, camera panning, drag selection box, particle effects and combat (both ranged and close quarters). 
I also implemented the novel parts of the game, which set it apart from the rest: the rainstorms which spawn enemies and destroy your units and structures, the wall system which allows the user to build connections on the vertices of the grid to shelter their units and structures if enclosed.

## Controls: 

All modes:
- Hold middle mouse to pan
- Press B to enter build mode
- Press F to enter wall mode
- Press ESC to pause

Game mode:
- Click on a building to train units or demolish it
- Select units with left mouse, or drag box to select (hold shift to combine selections)
- Right click to command units

Build mode:
- Drag and drop buildings onto the grid from the bottom left to build them
- Press B to exit build mode

Wall mode:
- Drag a straight line from vertices to create walls between them
- Right click wall to delete it
- Press G over a connection to turn it into a gate
- Press F to exit wall mode

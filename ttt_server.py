# Import the socket module
import socket
# Import multi-threading module
import threading
# Import the time module
import time
# Import command line arguments
from sys import argv

# If there are more than 2 arguments 
if(len(argv) >= 2):
	# Set port number to argument 1
	port_number = argv[1];
else:
	# Ask the user to input port number
	port_number = input("Please enter the port:");

# Create the socket object, the first parameter AF_INET is for IPv4 networking, the second identifies the socket type, SOCK_STREAM is for TCP protocal
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM);

# Keep repeating connecting to the server
while True:
	try:
		# Bind to an address (localhost) with the designated port 
		server_socket.bind(("localhost", int(port_number)));
		print("Reserved port ", port_number);

		# Start listening to the binded address
		server_socket.listen(1);
		print("Listening to port ", port_number);

		# Break the while loop if no error is caught
		break;

	except:
		# Caught an error
		print("There is an error when trying to bind localhost::", port_number);

		# Ask the user what to do with the error
		choice = input("[A]bort, [C]hange port, or [R]etry?");

		if(choice.lower() == "a"):
			exit();
		elif(choice.lower() == "c"):
			port_number = input("Please enter the port:");

# Define the Player class
class Player:
	def sendMatchInfo(self):
		self.connection.send(("You are now matched with player " + str(self.match.id) + "\nGame is getting started!\nYou are the \"" + self.role + "\"").encode());


# Define the Game class
class Game:
	pass;

# Create an array object to store connected players
players = [];

# Use a simple lock to synchronize access
lock_matching = threading.Lock();
# This function is to match a player with another one
def matchingPlayer(player):
	# Try acquiring the lock
	lock_matching.acquire();
	try:
		# Loop through each player
		for p in players:
			# If another player is found waiting and its not the player itself
			if(p.isWaiting and p is not player):
				# Matched player with p
				# Set their match
				player.match = p;
				p.match = player;
				# Set their roles
				player.role = "X";
				p.role = "O";
				# Set the player is not waiting any more
				player.isWaiting = False;
				p.isWaiting = False;
				# Then return the player's ID
				return p;
	finally:
		# Release the lock
		lock_matching.release();
	# Return None if nothing is found
	return None;

# Check if the player wins the game. Return value - 1: Win; 0:Draw; -1:No result yet
def checkWinner(game, player):
	s = game.board_content;

	# Check columns
	if(len(set([s[0], s[1], s[2], player.role])) == 1):
		return 1;
	if(len(set([s[3], s[4], s[5], player.role])) == 1):
		return 1;
	if(len(set([s[6], s[7], s[8], player.role])) == 1):
		return 1;

	# Check rows
	if(len(set([s[0], s[3], s[6], player.role])) == 1):
		return 1;
	if(len(set([s[1], s[4], s[7], player.role])) == 1):
		return 1;
	if(len(set([s[2], s[5], s[8], player.role])) == 1):
		return 1;

	# Check diagonal
	if(len(set([s[0], s[4], s[8], player.role])) == 1):
		return 1;
	if(len(set([s[2], s[4], s[6], player.role])) == 1):
		return 1;

	# If there's no empty position left, draw
	if " " not in s:
		return 0;

	# The result cannot be determined yet
	return -1;

# Make a move
def gameMove(game, moving_player, waiting_player):
	# Send both players the current board content
	moving_player.connection.send(("".join(game.board_content)).encode());
	waiting_player.connection.send(("".join(game.board_content)).encode());
	# Let the moving player move, Y stands for yes it's turn to move, and N stands for no and waiting
	moving_player.connection.send("Y".encode());
	waiting_player.connection.send("N".encode());
	# Receive the move from the moving player
	move = int(moving_player.connection.recv(1).decode());
	# Send the move to the waiting player
	waiting_player.connection.send(str(move).encode());
	# Write the "X" into the board
	game.board_content[move - 1] = moving_player.role;
	# Check if this will result in a win
	result = checkWinner(game, moving_player);
	if(result != -1):
		if(result == 0):
			moving_player.connection.send(("".join(game.board_content)).encode());
			waiting_player.connection.send(("".join(game.board_content)).encode());
			moving_player.connection.send("D".encode());
			waiting_player.connection.send("D".encode());
			return True;
		if(result == 1):
			moving_player.connection.send(("".join(game.board_content)).encode());
			waiting_player.connection.send(("".join(game.board_content)).encode());
			moving_player.connection.send("W".encode());
			waiting_player.connection.send("L".encode());
			return True;
		return False;

def gameThread(game):
	# Send both players the match info
	game.player1.sendMatchInfo();
	game.player2.sendMatchInfo();

	# Print the match info onto screen 
	print("Player " + str(game.player1.id) + " is matched with player " + str(game.player2.id) + "\n");

	if(game.player1.connection.recv(1024).decode() == "Ready" and game.player2.connection.recv(1024).decode() == "Ready"):
		print("New game started!");
	else:
		print("Error occured.");

	while True:
		# Player 1 move
		if(gameMove(game, game.player1, game.player2)):
			return;
		# Player 2 move
		if(gameMove(game, game.player2, game.player1)):
			return;


# The client thread for each player 
def clientThread(player):
	# Send the welcome message back to the client
	player.connection.send(("Welcome to Tic Tac Toe online, player " + str(player.id) + "\nPlease wait for another player to join the game...").encode());

	while True:
		# If the player is still waiting for another player to join
		if(player.isWaiting):
			# Try to match this player with other waiting players
			match_result = matchingPlayer(player);

			if(match_result is None):
				# If not matched, wait for a second (to keep CPU usage low) and keep trying
				time.sleep(1);
			else:
				# If matched with another player

				# Initialize a new Game object to store the game's infomation
				new_game = Game();
				# Assign both players
				new_game.player1 = player;
				new_game.player2 = match_result;
				# Create an empty string for empty board content
				new_game.board_content = list("         ");

				# This thread then deals with the game instead
				gameThread(new_game);

				# End this thread
				return;
		else:
			# If the player has already got matched, end this thread
			return;

		
# Loop to infinitely accept new clients
while True:
	# Accept a connection from a client
	connection, client_address = server_socket.accept();
	print("Received connection from ", client_address);

	# Initialize a new Player object to store all the client's infomation
	new_player = Player();
	# Generate an id for the client
	new_player.id = len(players) + 1;
	# Assign the corresponding connection 
	new_player.connection = connection;
	# Assign the corresponding client address 
	new_player.client_address = client_address;
	# Set the player waiting status to True
	new_player.isWaiting = True;
	# Push this new player object into the players array
	players.append(new_player);

	# Start a new thread to deal with this client
	threading.Thread(target=clientThread, args=(new_player,)).start();

# Close the socket
server_socket.close();
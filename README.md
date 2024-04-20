# Ramat-Kal Trivia
Welcome to Ramat-Kal - a trivia game that determines who is the best israeli chief of general staff of all time.
This is a client-server application which implements a trivia contest between all the israeli chief of general staff which are the players.
The players in the game get a random fact about israel, which is either true or false, and are supposed to answer correctly as fast as possible.
##Game Flow
1. Run clients (2 or more) as the number of players you want, and a server
2. Wait until the clients are connected to the server.
3. Once the game started, each client recieve a random fact about israel, which is true or false, and should answer it correctly as fast as possible (view Notes 1,2).
4. If a player answered the question correctly - the game ends and the player wins immediatley.
5. If a player answered the question incorrectly - he will be disqualified from this round, and wait until all other players answers \ the round finish (view note 3).
6. If all players answered the question incorrectly or no one answered the question - they are all disqualified and they will be given another question.
7. After the game is decided, the server sends a summary message to all players and a new game is started.

## Game Statistics
After each game finished, the server displays staistics about all the games that have been played since the server started:
1. For the player who won the game, the server represent to all the players if the player that won the game was the fastest to answer this question.
2. The server displays the question that most players have answered incorrectly until now - which is marked as the hardest question.

## Game Colors
The command prompt consists colors for more intuitive, comprehensive and fun game. each color describes the following:
1. statistics will be shown in light blue
2. warnings and notes by the game will be shown in yellow
3. Correct answers and happy cases will be shown in green
4. wrong answers and errors will be shown in red.

## Notes
1. Possible answers for true: T,Y,1.
2. Possible answers for false: F,N,0.
3. There is 10 seconds to answer each question.
4. Game is over after a question is answered correctly.
5. both server and clients run forever, until you quit them manually.

![image](https://github.com/assayagt/TriviaProject/assets/104003703/8d144326-49bb-4a05-8411-7378a9c0c890)


### Have fun!

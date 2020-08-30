from flask import Flask, render_template, flash, redirect, url_for, request, session,logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, IntegerField
from wtforms.fields.html5 import DateField, DateTimeField
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
app.debug = True 
#initial creation of database
#testing
def creation():
	#Create cursor
	cur = mysql.connection.cursor()
	
	#Create database
	cur.execute("CREATE DATABASE IF NOT EXISTS leaguedb;")
	
	#Use database
	cur.execute("USE leaguedb;")
	
	#Create manager table
	cur.execute("CREATE TABLE IF NOT EXISTS managers(manager_id INT NOT NULL AUTO_INCREMENT, username VARCHAR(100) UNIQUE NOT NULL, email VARCHAR(100) UNIQUE NOT NULL, password VARCHAR(250) NOT NULL, PRIMARY KEY (manager_id));")
	
	#Create sport type table
	cur.execute("CREATE TABLE IF NOT EXISTS sport_type(type varchar(100) UNIQUE NOT NULL);")
	
	#Create sport table
	cur.execute("CREATE TABLE IF NOT EXISTS sports (sport_id INT NOT NULL AUTO_INCREMENT, sport_name VARCHAR(100) NOT NULL, type VARCHAR(250) NOT NULL, PRIMARY KEY(sport_id), FOREIGN KEY (type) REFERENCES sport_type(type));")
	
	#Create league table
	cur.execute("CREATE TABLE IF NOT EXISTS leagues(league_id INT NOT NULL AUTO_INCREMENT, league_name VARCHAR(100) NOT NULL, no_of_divisions INT NOT NULL, start_date VARCHAR(100) NOT NULL, end_date VARCHAR(100) NOT NULL, manager_id INT NOT NULL, sport_id INT NOT NULL, PRIMARY KEY(league_id), FOREIGN KEY (manager_id) REFERENCES managers(manager_id), FOREIGN KEY (sport_id) REFERENCES sports(sport_id));")
	
	#Create division table
	cur.execute("CREATE TABLE IF NOT EXISTS divisions(division_id INT NOT NULL AUTO_INCREMENT, division_name VARCHAR(200) NOT NULL, league_id INT NOT NULL, PRIMARY KEY(division_id), FOREIGN KEY(league_id) REFERENCES leagues(league_id));")
	
	#Create teams table
	cur.execute("CREATE TABLE IF NOT EXISTS teams (team_id INT NOT NULL AUTO_INCREMENT, team_name VARCHAR(100) NOT NULL, standing VARCHAR(100) NOT NULL, division_id INT NOT NULL, league_id INT NOT NULL, PRIMARY KEY (team_id), FOREIGN KEY (division_id) REFERENCES divisions(division_id), FOREIGN KEY (league_id) REFERENCES leagues(league_id));")
	
	#Create plays table
	cur.execute("CREATE TABLE IF NOT EXISTS plays(team_id_A INT NOT NULL, team_id_B INT NOT NULL, schedule VARCHAR(100), score_A INT NOT NULL, score_B INT NOT NULL, match_id INT AUTO_INCREMENT, division_id INT NOT NULL, league_id INT NOT NULL, PRIMARY KEY(match_id), FOREIGN KEY(team_id_A) REFERENCES teams(team_id), FOREIGN KEY (team_id_B) REFERENCES teams(team_id), FOREIGN KEY (league_id) REFERENCES leagues(league_id), FOREIGN KEY (division_id) REFERENES divisions(division_id));")
	
	#Create player table
	cur.execute("CREATE TABLE IF NOT EXISTS players(player_id INT NOT NULL AUTO_INCREMENT, player_name VARCHAR(200) NOT NULL, age INT NOT NULL, team_id INT NOT NULL, division_id INT NOT NULL, league_id INT NOT NULL, PRIMARY KEY(player_id), FOREIGN KEY (team_id) REFERENCES teams(team_id), FOREIGN KEY (division_id) REFERENCES divisions(division_id), FOREIGN KEY (league_id) REFERENCES leagues(league_id);")
	
	
	

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'JeCEVd7Vwg3z!'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# mysql = MySQL(app)
# with app.app_context():
	# creation()
app.config['MYSQL_DB'] = 'leaguedb'

# init MYSQL
mysql = MySQL(app)



#Route to home/index page
@app.route('/')
def index():
	return render_template('home.html')

#Route to about page
@app.route('/about')
def about():
	return render_template('about.html')
	
#Defining class of registration form
class RegisterForm(Form):
	username = StringField('Username', [validators.Length(min=6, max=100)])
	email = StringField('Email Address', [validators.Length(min=10, max=100)])
	password = PasswordField('Password', [validators.Length(min=8, max=250), 
	validators.DataRequired(), 
	validators.EqualTo('confirm', message="Passwords do not match"),
	])
	confirm = PasswordField('Confirm Password')

#Route for adding managers
@app.route('/register', methods = ['GET', 'POST'])
def register_manager():
		# Create cursor
		cur = mysql.connection.cursor()
		form = RegisterForm(request.form)
		if request.method == 'POST' and form.validate():
			username = form.username.data
			email = form.email.data
			password = sha256_crypt.encrypt(str(form.password.data))
			
			uexists = cur.execute ("SELECT * FROM managers WHERE username = '{0}'" .format(username))
			
			eexists = cur.execute ("SELECT * FROM managers WHERE email = '{0}'" .format(email))
			
			if (uexists == True):
				flash('Username already in use', 'danger')
				return redirect(url_for('register_manager'))
			elif (eexists == True):
				flash('Email Address already in use', 'danger')
				return redirect(url_for('register_manager'))
			else:
				
				cur.execute("INSERT INTO managers(username, email, password) VALUES(%s, %s, %s)", (username, email, password))
				
				# Commit to DB
				mysql.connection.commit()
				
				# Close connection 
				cur.close()
				
				flash('Registration successful!', 'success')
				
				return redirect(url_for('register_manager'))
		return render_template('register_manager.html', form=form)
		
#Route for displaying courses
@app.route('/courses')
def courses():
	#Create cursor 
	cur = mysql.connection.cursor()
	
	#Get courses
	result = cur.execute("SELECT * FROM courses")
	
	courses = cur.fetchall()
	
	if result > 0:
		return render_template('courses.html', courses = courses)
	else:
		msg = 'No records found.'
		return render_template('courses.html',msg=msg)
	
	#Close connection
	cur.close()
	
	
#Route for deleting students in database
@app.route('/delete_student/<string:id>', methods =["POST"])
def delete_student(id):
	#Create cursor
	cur = mysql.connection.cursor()
	
	#Execute
	cur.execute("DELETE FROM students WHERE id = %s", [id])
	
	#Commit to DB
	mysql.connection.commit()
	
	#Close connection
	cur.close()
	
	flash("Student deleted.", 'success')
	
	return redirect(url_for('students'))
	
#Route for logging in
@app.route('/login', methods = ['GET', 'POST'])
def login():
	if request.method == 'POST':
		#Get form fields
		username = request.form['username']
		password_candidate = request.form['password']
		
		#Create cursor
		cur = mysql.connection.cursor()
		
		#Look for manager by username
		result = cur.execute("SELECT * FROM managers WHERE username = %s", [username])
		
		if result > 0:
			#Get stored hash
			data = cur.fetchone()
			password = data['password']
			manager_id = data['manager_id']
			
			#Compare passwords
			if sha256_crypt.verify(password_candidate, password):
				#Passed
				session['logged_in'] = True
				session['username'] = username
				session['manager_id'] = manager_id
			
				flash("You are now logged in!", 'success')
				return redirect(url_for('dashboard'))
			else:
				flash("Invalid login", 'danger')
				return redirect(url_for('login'))
			
			#Close the connection
			cur.close()
		else:
			flash("Username not found", 'danger')
			return redirect(url_for('login'))
			
	return render_template('login.html')

#Check if user is logged in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash("You are unauthorized. Please login.", "danger")
			return redirect(url_for('login'))
	return wrap
	
#Logout
@app.route('/logout')
def logout():
		session.clear()
		flash("You are now logged out", "success")
		return redirect(url_for('login'))
	
#Dashboard route
@app.route('/dashboard', methods = ['GET'])
@is_logged_in
def dashboard():
	#Define manager_id
	manager_id = session['manager_id']
	#Create cursor
	cur = mysql.connection.cursor()
	
	#Get leagues
	result = cur.execute("SELECT leagues.league_id, leagues.league_name, leagues.start_date, leagues.end_date, leagues.no_of_divisions, sports.sport_name FROM leagues LEFT JOIN sports ON leagues.sport_id = sports.sport_id WHERE leagues.manager_id = %s;",[manager_id])
	 
	
	
	leagues = cur.fetchall()
	
	
	# print(leagues)
	if result > 0:
		return render_template('dashboard.html', leagues=leagues)
		
	else:
		msg = 'No leagues found'
		return render_template('dashboard.html')
		
	#Close connection
	cur.close()
	return render_template('dashboard.html')

#Defining class of league form
class LeagueForm(Form):
	league_name = StringField('League Name', [validators.Length(min=6, max=100)])
	no_of_divisions = IntegerField('Number of Divisions')#[validators.Length(min=1, max=11)])
	start_date = DateField('Start Date', format = '%Y-%m-%d')
	end_date = DateField('End Date', format = '%Y-%m-%d')
	sport_id = IntegerField('Sport ID')# [validators.Length(min = 1, max = 11)])
	
#Add League
@app.route('/add_league', methods = ['GET', 'POST'])
@is_logged_in
def add_league():
	form = LeagueForm(request.form)
	#Create cursor
	cur = mysql.connection.cursor()
		
	#Grab all sports
	result = cur.execute("SELECT * from sports;")
		
	sports = cur.fetchall()
	if request.method == 'POST' and form.validate():
	
		#Call forms 
		league_name = form.league_name.data
		no_of_divisions = form.no_of_divisions.data
		start_date = form.start_date.data
		end_date = form.end_date.data
		sport_id = form.sport_id.data
		
		#Add to database
		cur.execute("INSERT INTO leagues (league_name, no_of_divisions, start_date, end_date, sport_id, manager_id) VALUES (%s, %s, %s, %s, %s, %s)", (league_name, no_of_divisions, start_date, end_date, sport_id, session['manager_id']))
		
		#Commit to DB
		mysql.connection.commit()
		
		#Close connection
		cur.close()
		
		flash("League Created!", 'success')
		
		return redirect(url_for('dashboard'))
	return render_template('add_league.html', form=form, sports=sports)	

#Edit League
@app.route('/edit_league/<string:league_id>', methods = ['GET','POST'])
def edit_league(league_id):
	session['league_id'] = league_id
	#Create cursor
	cur = mysql.connection.cursor()
	
	#Get divisions
	result = cur.execute("SELECT * FROM divisions WHERE league_id = %s", [league_id])
	
	divisions = cur.fetchall()
	
	cur.close()
	
	if result > 0:
		return render_template('edit_league.html', divisions = divisions)
	else:
		msg = 'No divisions found'
		return render_template('edit_league.html')

#Route for deleting leagues in database
@app.route('/delete_league/<string:league_id>', methods =['POST', 'GET'])
def delete_league(league_id):
	#Create cursor
	cur = mysql.connection.cursor()
	
	#Execute
	cur.execute("DELETE FROM plays WHERE league_id = %s", [league_id])
	cur.execute("DELETE FROM players WHERE league_id = %s", [league_id])
	cur.execute("DELETE FROM teams WHERE league_id = %s", [league_id])
	cur.execute("DELETE FROM divisions WHERE league_id = %s", [league_id])
	cur.execute("DELETE FROM leagues WHERE league_id = %s", [league_id])
	
	
	#Commit to DB
	mysql.connection.commit()
	
	#Close connection
	cur.close()
	
	flash("League deleted.", 'success')
	
	#Dashboard is placeholder
	return redirect(url_for('dashboard'))

	
#Defining class for division form
class DivisionForm(Form):
	division_name = StringField('Division Name', [validators.Length(min=6, max=200)])
	
#Add Division
@app.route('/add_division/<string:league_id>', methods=['GET', 'POST'])
def add_division(league_id):
	form = DivisionForm(request.form)
	league_id = session['league_id']
	if request.method == 'POST' and form.validate():
		division_name = form.division_name.data
	
		#Create cursor
		cur = mysql.connection.cursor()
	
		#Add to database
		cur.execute("INSERT INTO divisions (division_name, league_id) VALUES (%s, %s)", (division_name, league_id))
	
		#Commit to DB
		mysql.connection.commit()
	
		#Close connection
		cur.close()
	
		flash("Division created!", 'success')
	
		#Dashboard is placeholder
		return redirect(url_for('dashboard'))
	return render_template('add_division.html', form=form)
	

#Route for deleting divisions in database
@app.route('/delete_division/<string:division_id>', methods =['POST','GET'])
def delete_division(division_id):
	#Create cursor
	cur = mysql.connection.cursor()
	
	#Execute
	cur.execute("DELETE FROM plays WHERE division_id = %s", [division_id])
	cur.execute("DELETE FROM players WHERE division_id = %s", [division_id])
	cur.execute("DELETE FROM teams WHERE division_id = %s", [division_id])
	cur.execute("DELETE FROM divisions WHERE division_id = %s", [division_id])
	
	#Commit to DB
	mysql.connection.commit()
	
	#Close connection
	cur.close()
	
	flash("Division deleted.", 'success')
	
	#Dashboard is placeholder
	return redirect(url_for('dashboard'))
	
	
class TeamForm(Form):
	team_name = StringField("Team Name", [validators.Length(min = 6, max =100)])
	
#Route for adding teams per division
@app.route('/edit_division/<string:division_id>', methods = ['POST','GET'])
@is_logged_in
def edit_division(division_id):
	form = TeamForm(request.form)
	session['division_id'] = division_id
		
	#Create cursor
	cur = mysql.connection.cursor()
	
	#Get teams
	result = cur.execute("SELECT * FROM teams WHERE division_id = %s", [division_id])
		
	teams = cur.fetchall()
	
	#Get plays
	results = cur.execute("SELECT pl.team_id_A, pl.team_id_B, pl.schedule, pl.score_A, pl.score_B, pl.match_id, team_A.team_name AS team_name_A, team_B.team_name AS team_name_B FROM plays AS pl LEFT JOIN teams AS team_A ON pl.team_id_A = team_A.team_id LEFT JOIN teams AS team_B ON pl.team_id_B = team_B.team_id WHERE pl.division_id = %s;", [division_id])
	
	plays = cur.fetchall()
	
	#Close connection
	cur.close()
	
	if result > 0:
		return render_template('edit_division.html', teams = teams, plays = plays)
	else:
		msg = 'No teams found'
		return render_template('edit_division.html')
		
	

#Add team route
@app.route('/add_team/<string:division_id>', methods = ['POST', 'GET'])
@is_logged_in
def add_team(division_id):
	league_id = session['league_id']
	form = TeamForm(request.form)
	division_id = session['division_id']
	
	if request.method == 'POST' and form.validate():
		team_name = form.team_name.data
		
		#Create cursor
		cur = mysql.connection.cursor()
		
		#Add to database
		cur.execute("INSERT INTO teams (team_name, division_id, league_id) VALUES (%s, %s, %s)", (team_name, division_id, league_id))
		
		#Commit to DB
		mysql.connection.commit()
		
		#Close connection
		cur.close()
		
		flash("Team created!", 'success')
		
		#Piste nga dashboard placeholder gihapon
		return redirect(url_for('dashboard'))
	return render_template('add_team.html', form=form)
	
#Edit team route
@app.route('/edit_team/<string:team_id>', methods = ['POST', 'GET'])
@is_logged_in
def edit_team(team_id):
	
	session['team_id'] = team_id
	
	#Create cursor
	cur = mysql.connection.cursor()
	
	#Get teammates
	result = cur.execute("SELECT * FROM players WHERE team_id = %s", [team_id])
	
	players = cur.fetchall()
	
	cur.close()
	
	if result > 0:
		return render_template('edit_team.html', players=players)
	else:
		msg = 'No players found'
		return render_template('edit_team.html')
		
#Route for deleting teams in database
@app.route('/delete_team/<string:team_id>', methods =['POST','GET'])
def delete_team(team_id):
	#Create cursor
	cur = mysql.connection.cursor()
	
	#Execute
	cur.execute("DELETE FROM plays WHERE team_id_A = %s", [team_id])
	cur.execute("DELETE FROM plays WHERE team_id_B = %s", [team_id])
	cur.execute("DELETE FROM players WHERE team_id = %s", [team_id])
	cur.execute("DELETE FROM teams WHERE team_id = %s", [team_id])
	
	#Commit to DB
	mysql.connection.commit()
	
	#Close connection
	cur.close()
	
	flash("Team deleted.", 'success')
	
	#Dashboard is placeholder
	return redirect(url_for('dashboard'))
	
		
#Player Form
class PlayerForm(Form):
	player_name = StringField("Player Name", [validators.Length(min = 6, max =100)])
	age = IntegerField("Age")

#Add player to team
@app.route('/add_player/<string:team_id>', methods = ['POST', 'GET'])
@is_logged_in
def add_player(team_id):
	division_id = session['division_id']
	league_id = session['league_id']
	team_id = session['team_id']
	form = PlayerForm(request.form)
	print(team_id)
	print(division_id)
	print(league_id)
	if request.method == 'POST' and form.validate():
		player_name = form.player_name.data
		age = form.age.data
		
		#Create cursor
		cur = mysql.connection.cursor()
		
		#Add to database
		cur.execute("INSERT INTO players (player_name, age, team_id, division_id, league_id) VALUES (%s, %s, %s, %s, %s)", (player_name, age, team_id, division_id, league_id))
		
		#Commit to DB
		mysql.connection.commit()
		
		#Close connection
		cur.close()
		
		flash("Player has been saved to team!", 'success')
		
		#Dashboard redirect
		return redirect(url_for('dashboard'))
	return render_template('add_player.html', form = form)
	
#Route for deleting players in database
@app.route('/delete_player/<string:player_id>', methods=['POST','GET'])
def delete_player(player_id):
	#Create cursor
	cur = mysql.connection.cursor()
	
	#Execute
	cur.execute("DELETE FROM players WHERE player_id = %s", [player_id])
	
	#Commit to DB
	mysql.connection.commit()
	
	#Close connection
	cur.close()
	
	flash("Team deleted.", 'success')
	
	#Dashboard is placeholder
	return redirect(url_for('dashboard'))
	
	
#Route for all leagues
@app.route('/all_leagues', methods = ['GET'])
def all_leagues():
	#Create cursor
	cur = mysql.connection.cursor()
	
	#Get leagues
	result = cur.execute ("SELECT leagues.league_id, leagues.league_name, leagues.start_date, leagues.end_date, leagues.no_of_divisions, leagues.manager_id, sports.sport_name FROM leagues LEFT JOIN sports ON leagues.sport_id = sports.sport_id;")
	
	leagues = cur.fetchall()
	
	if result > 0:
		return render_template('all_leagues.html', leagues=leagues)
		
	else:
		msg = 'No leagues found'
		return render_template('all_leagues.html')
		
	#Close connection
	cur.close()
	return render_template('all_leagues.html')

#Route for viewing league information
@app.route('/view_league/<string:league_id>', methods=['GET'])
def view_league(league_id):
	session['league_id'] = league_id
	
	#Create cursor
	cur = mysql.connection.cursor()
	
	#Get divisions
	result = cur.execute("SELECT * FROM divisions WHERE league_id = %s", [league_id])
	
	divisions = cur.fetchall()
	
	#Close cursor
	cur.close()
	
	if result > 0:
		return render_template('view_league.html', divisions = divisions)
	else:
		msg = 'No divisions found'
		return render_template('view_leagues.html')

#Route for viewing division information
@app.route('/view_division/<string:division_id>', methods=['GET'])
def view_division(division_id):
	session['division_id'] = division_id
	
	#Create cursor
	cur = mysql.connection.cursor()
	
	#Get teams in division
	result = cur.execute("SELECT * FROM teams WHERE division_id = %s", [division_id])
	
	teams = cur.fetchall()
	
	#Get plays in division
	results = cur.execute("SELECT pl.team_id_A, pl.team_id_B, pl.schedule, pl.score_A, pl.score_B, pl.match_id, team_A.team_name AS team_name_A, team_B.team_name AS team_name_B FROM plays AS pl LEFT JOIN teams AS team_A ON pl.team_id_A = team_A.team_id LEFT JOIN teams AS team_B ON pl.team_id_B = team_B.team_id WHERE pl.division_id = %s;", [division_id])
	
	plays = cur.fetchall()
	
	#Close cursor
	cur.close()
	
	if result > 0:
		return render_template('view_division.html', teams = teams, plays=plays)
	else:
		msg = 'No divisions found'
		return render_template('view_division.html')
		
#Route for viewing team information
@app.route('/view_team/<string:team_id>', methods = ['GET'])
def view_team(team_id):
	session['team_id'] = team_id
	
	#Create cursor
	cur = mysql.connection.cursor()
	
	#Get players in team
	result = cur.execute("SELECT * FROM players WHERE team_id = %s", [team_id])
	
	players = cur.fetchall()
	
	#Close cursor
	cur.close()
	
	if result > 0:
		return render_template('view_team.html', players = players)
	else:
		msg = 'No players found'
		return render_template('view_team.html')

#Add Play form
class PlayForm(Form):
	team_id_A = IntegerField("Team ID A")
	team_id_B = IntegerField("Team ID B")
	schedule = DateField('Schedule', format = '%Y-%m-%d')
	score_a = IntegerField("Team A Score")
	score_b = IntegerField("Team B Score")
		
	
#Route for adding plays
@app.route('/add_play/<string:division_id>', methods = ['GET', 'POST'])
@is_logged_in
def add_play(division_id):
	division_id = session['division_id']
	league_id = session['league_id']
	form = PlayForm(request.form)
	
	#Create cursor
	cur = mysql.connection.cursor()
	
	#Pull teams
	results = cur.execute ("SELECT * FROM teams WHERE division_id = %s", [division_id])
		
	teams = cur.fetchall()
	
	#Close connection
	cur.close()
		
	
	if request.method == 'POST' and form.validate():
		team_id_A = form.team_id_A.data
		team_id_B = form.team_id_B.data
		schedule = form.schedule.data
		score_a = form.score_a.data
		score_b = form.score_b.data
		
		#Create cursor
		cur = mysql.connection.cursor()
		
		#Add to database
		cur.execute("INSERT INTO plays (team_id_A, team_id_B, schedule, score_a, score_b, division_id, league_id) VALUES (%s, %s, %s, %s, %s, %s, %s)", (team_id_A, team_id_B, schedule, score_a, score_b, division_id, league_id))
		
		#Commit to DB
		mysql.connection.commit()
		
		#Close connection
		cur.close()
		
		flash("Game has been created!", 'success')
		
		#Dashboard Redirect
		return redirect(url_for('dashboard'))
	return render_template('add_play.html', form=form, teams=teams)
		
	

if __name__ == '__main__':
	app.secret_key = 'secretkey'
	app.run()
	

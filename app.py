#Initialises the libraries for the application
import requests
import sqlite3
from flask import Flask, render_template, redirect, flash, session, request
from bokeh.plotting import figure
from bokeh.embed import components
import random

# Initialize Flask application
app = Flask(__name__)

app.secret_key = "super secret key"
api_key = "07639ce6679d61f3365f70183d1369e4"
github = "https://github.com/devhogosha"
source_code = "https://github.com/devhogosha/weatherforcast"

#connects to database, retrieves all city names, stores in option
conn = sqlite3.connect('weather.db')
cursor = conn.cursor()
cursor.execute("SELECT city FROM weather_data")
global options 
options = cursor.fetchall()
cursor.fetchall()
conn.close()

# Define function to get weather data from API and store in database
def get_weather_data(city):
    
    # Update API parameters with city name
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    # Make API request and get response
    response = requests.get(url) 
    data = response.json()

    # Connect to database and create table if it does not exist
    conn = sqlite3.connect("weather.db")
    c = conn.cursor()
    #c.execute("DROP TABLE weather_data")
    c.execute("""CREATE TABLE IF NOT EXISTS weather_data
                 (city TEXT, date DATETIME, condition TEXT, description TEXT, temperature REAL, humidity REAL, pressure REAL, wind_speed REAL)""")

    # Insert weather data into database
    date = data["dt"]
    temperature = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    wind_speed = data["wind"]["speed"]
    condition = data["weather"][0]["main"]
    description = data["weather"][0]["description"]

    c.execute("SELECT city FROM weather_data WHERE city=?", (city,))
    data = c.fetchall()
    if data:
        c.execute("UPDATE weather_data SET city=?, date=DATETIME(?, 'auto'), condition=?, description=?, temperature=?, humidity=?, pressure=?, wind_speed=? WHERE city=? ", (city, date, condition, description, temperature, humidity, pressure, wind_speed, city))
        conn.commit()
    else:
        c.execute("INSERT INTO weather_data VALUES (?, DATETIME(?, 'auto'), ?, ?, ?, ?, ?, ?)", (city, date, condition, description, temperature, humidity, pressure, wind_speed))
        conn.commit()
    conn.close()


# Define function to display weather data on graph
def display_weather_data(city):
    # Connect to database and get weather data
    conn = sqlite3.connect("weather.db")
    c = conn.cursor()
    c.execute("SELECT * FROM weather_data WHERE city=?", (city,))
    global data_result
    data_result = c.fetchall()
    conn.close()

#Defines plot route for displaying weather data on graphs
@app.route("/plot", methods=["POST"])
def plot():
    conn = sqlite3.connect("weather.db")
    cursor = conn.cursor()
    selected_option = request.form.getlist("option")
    plot_option = request.form.get("select_plot")
    plot_options = ["scatter plot", "bar chart", "line plot"]
    
    temp_data = []

    for city in selected_option:
        cursor.execute("SELECT temperature FROM weather_data where city=?", (city,))
        temp = cursor.fetchone()
        temp_data.append(temp)
    conn.close()
    
    #Converting temperature data from tuple
    plot_temp_data = [x[0] for x in temp_data]
    colors = [f"#{random.randint(0, 0xFFFFFF):06x}" for i in range(len(plot_temp_data))]


    if (len(selected_option) > 1) and (plot_option in plot_options) :
        # create a new plot with a title and axis labels
        match plot_option:
            case "scatter plot":
                plot = figure(x_range=selected_option, title=f"{plot_option.title()} Showing Daily Temperature Against Each City", x_axis_label="CITIES", y_axis_label="DAILY WEATHER TEMPERATURE °C", toolbar_location=None,
                                tools="hover",tooltips=[("City", "@x"), ("Temperature", "@y°C")],  width =1080, height = 720)
                plot.circle(x=selected_option, y=plot_temp_data, size=15, line_color=None, fill_color=colors)
                script, div = components(plot)
                return render_template("plot.html", script=script, div=div, ploty=plot_option, source_code=source_code)
            case "bar chart":
                plot = figure(x_range=selected_option, title=f"{plot_option.title()} Showing Daily Temperature Against Each City", x_axis_label="CITIES", y_axis_label="DAILY WEATHER TEMPERATURE °C", toolbar_location=None,
                                tools="hover",tooltips=[("City", "@x"), ("Temperature", "@top°C")],  width =1080, height = 720)
                plot.vbar(x=selected_option, top=plot_temp_data, color=colors, width=0.5)
                script, div = components(plot)
                return render_template("plot.html", script=script, div=div, ploty=plot_option, source_code=source_code)
            case "line plot":
                plot = figure(x_range=selected_option, title=f"{plot_option.title()} Showing Daily Temperature Against Each City", x_axis_label="CITIES", y_axis_label="DAILY WEATHER TEMPERATURE °C", toolbar_location=None,
                                tools="hover",tooltips=[("City", "@x"), ("Temperature", "@y°C")],  width =1080, height = 720)
                plot.line(x=selected_option, y=plot_temp_data, line_width=2)
                plot.circle(x=selected_option, y=plot_temp_data, size=8, line_color=None, fill_color=colors)
                script, div = components(plot)
                return render_template("plot.html", script=script, div=div, ploty=plot_option, source_code=source_code)
    else:
        flash("Please Select Two Or More Cities For Plotting")
        return redirect("/all_weather_report")

#Defines root route for displaying weather data
@app.route("/", methods=["GET", "POST"])
def weather_data():
    try:
        if request.method == "POST":
        
            session["city"] = request.form["city"].capitalize()
            stored_city = session.get("city", "No City Was Entered")
            
            get_weather_data(stored_city)
            display_weather_data(stored_city)
            
            return render_template("index.html",city=stored_city,data_result = data_result, github=github, source_code=source_code)
        else:
            return render_template("index.html", github=github, source_code=source_code)
    except:
        return render_template("index.html", github=github, source_code=source_code)

#Defines database route for displaying and plotting weather data
@app.route("/all_weather_report")
def all_weather_report():
    plot_options = ["scatter plot", "bar chart", "line plot"]
    conn = sqlite3.connect("weather.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM weather_data")
    all_weather_data = cursor.fetchall()
    conn.close()
    return render_template("all_weather_report.html", all_weather_data=all_weather_data, get_city_names=options, graph_names=plot_options, github=github, source_code=source_code)

#Defines delete route for deleting weather data
@app.route("/delete", methods=["POST"])
def delete():
    # Get the list of IDs to be deleted from the form data
    city_ids = request.form.getlist("city_id")
    if len(city_ids) >= 1:
        # Delete the selected rows from the database
        conn = sqlite3.connect("weather.db")
        conn.cursor()
        for city in city_ids:
            conn.execute("DELETE FROM weather_data WHERE city=?", (city,))
        conn.commit()
        conn.close()
        # Redirect the user back to the index page
        flash(f"{city_ids[:]} Successfully Deleted")
        return redirect("/all_weather_report")
    else:
        flash(f"Select From The Table To Delete")
        return redirect("/all_weather_report")

#Defines about route for displaying about page
@app.route("/about")
def about():
    introduction = """
    This is a mini project developed by Nicholas Adams Asare and Benedict Joe Asamoah
    in fulfiment of the requirements to complete 1st semester of level 300.
    The program is a web-based weather report data application that uses Flask 
    to display current weather data for various cities in a database table. The program uses the OpenWeatherMap API to gather weather data
    for each city entered by the user and store it in a SQLite database. The program also provides an option to plot the temperature 
    against the cities in various plot options using the Bokeh library.
    """
    description = """
    The application starts with an API request to OpenWeatherMap to retrieve the current weather data for a particular city a user enters.
    The application stores all data from the user's search results in the SQLite database and a Flask route retrieves all the cities from the database table
    and stores them in the global options list, if there are records in the database table, the application renders a new page show which users a table of all records
    of each city's daily weather report where the user can choose to delete records from that database table.
    The application also provides an option to plot the temperature data against the selected cities using various plot options such as scatter plot,
    bar chart, and line plot. The application uses the Bokeh library to create the plots. When the user submits the form, the application retrieves
    the temperature data from the database table and creates a plot based on the selected plot option."""

    limitations = """
    The program requires internet access to get weather data from OpenWeatherMap API."""

    return render_template("about.html", introduction=introduction, description=description, limitations=limitations, github=github, source_code=source_code)

# Run Flask application
if __name__ == '__main__':
    app.run()
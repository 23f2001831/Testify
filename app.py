from flask import Flask, render_template  #import flask module 

app = Flask(__name__)    #create an instance of the Flask class

@app.route('/')          
def index():
    return render_template('index.html', name='John')

if __name__ == '__main__':
    app.run(debug=True)  #run the application
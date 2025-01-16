# gallifreyan
This is a graphics editor designed for writing sentences in Doctor's Cot Gallifreyan, a writing system created by Brittany Goodman and inspired by the fictional Gallifreyan language:

https://doctorscotgallifreyan.com/ 

## Current Features
Sentence Support: Write and visualize sentences in Doctor's Cot Gallifreyan.

Resizable Elements: Adjust the size of words, syllables, and inner circles for better layout control.

Element Positioning: Move and reposition various components, including words, syllables, vowels, and consonants.

Image Export: Save your designs as PNG images for easy sharing and use.

Animation: Bring your sentences to life with animation feature and save them as animated GIFs.

## Future Plans
Punctuation and Number Support: Visualize numbers and punctuation marks.

Customization Options: Introduce additional features for enhanced customization.

SVG Export: Allow designs to be exported as SVG files for higher-quality and scalable outputs.

## How to Run the Program

To run the program, make sure you have Python 3.10 or later installed on your system. First, install the required dependencies by running:
```
pip install -r requirements.txt
```
Once the dependencies are installed, run the following command from the project's root directory:
```
python -m src.main
```
## How to Use the Features
Enter the phonetic representation of your sentence by clicking the consonant and vowel buttons. Separate words with spaces and syllables with dashes. You can also remove characters from the input field as needed.

- Moving Elements: Drag syllables, consonants, and vowels to reposition them.
- Resizing Syllables: Adjust a syllable's size - along with all consecutive syllables - by dragging its border.
- Resizing Inner Circles: Modify the size of a syllable's inner circle by dragging its border.
- Resizing Words: Drag the border of the largest syllable to resize the word. Adjust the word's outer circle by dragging its border.
- Moving Words: Move an entire word by dragging the largest syllable or the empty space inside the word.

(good luck figuring it out)

Toggle the animation by clicking the Animation button.

Export your design as a PNG or GIF via File → Export as...

## Demo
![demo](https://github.com/katekorobova/gallifreyan/blob/main/demo.gif)

Exported PNG:

![png](https://github.com/katekorobova/gallifreyan/blob/main/its_a_big_universe.png)

Exported GIF:

![gif](https://github.com/katekorobova/gallifreyan/blob/main/its_a_big_universe.gif)

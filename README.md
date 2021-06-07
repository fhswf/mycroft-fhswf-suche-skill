# <img src="https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/address-card.svg" card_color="#39659F" width="50" height="50" style="vertical-align:bottom"/> Mycroft FH-SWF Kontaktsuche
Dieser Skill ist als Teil der Bachelorarbeit von [Silvio Marra](https://github.com/12io) entstanden und lässt Mycroft eine Suche nach Kontaktdaten einer Person auf der [Webseite der FH-SWF](https://www.fh-swf.de/) durchführen.


## Über den Skill
_Damit der Skill auch nach Bedarf in andere Sprachen übersetzt werden kann, ist die Implementierung auf englisch gehalten. Das bezieht sich sowohl auf die Namensgebung der Dateien in den sprachabhängigen Unterordnern von ./locale sowie die Variablennamen und Kommentare im Quellcode._

_To provide multiple languages if needed, implementation is done in english. This includes all names of files inside language-based subdirectories as well as variables and comments of source code._

Der Skill implementiert die Intention, Kontaktdaten von Mitarbeitenden sowie Lehrpersonal, über die eingesetzte Webseitensuche der Fachhochschule abzufragen. Die Anfragen werden direkt an den Suchserver via HTTP POST gestellt, von dem eine Antwort im JSON-Format zurückgeliefert wird. Anhand der Antwort bereitet Mycroft die Daten vor und gibt eine Antwort auf die gestellte Frage.

## Beispielfragen
* "Wo finde ich Herrn Professor Doktor XYZ"
* "In welchem Büro sitzt Frau Professorin Doktorin XYZ"
* "Wo ist das Büro von XYZ"
* "An welchem standort finde ich XYZ"
* "Wo kann ich XYZ antreffen"

## Credits
Silvio Marra <marra.silvio@fh-swf.de>

## Category
**Information**

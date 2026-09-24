# NOTE

Fichier contenant les tests de la fonctionnalité chauffeur, particulièrement pour les tâches et les services de Grade.

Pour lancer les tests, il faut utiliser la commande suivante :
- python manage.py test drivers.tests.test_tasks.GradeTaskTests -v 2 --settings=core.settings_dev
- python manage.py test drivers.tests.test_services.GradeServiceTests -v 2 --settings=core.settings_dev
- python manage.py test drivers.tests.test_views.GradeAPITests -v 2 --settings=core.settings_dev
- python manage.py test drivers.tests.test_models.GradeModelTests -v 2 --settings=core.settings_dev

La structure est simple, il faut juste ajouter le fichier de test dans le dossier tests et le nommer test_xxxx. 
L'option settings est pour préciser le fichier de settings à utiliser. En développement, on utilise core.settings_dev, crée ton fichier de config settings_dev et évite de travailler ou modifier directement le fichier settings.py, il est que pour la prod

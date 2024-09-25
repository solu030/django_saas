import django_env
from web import models
def run():
    models.PricePolicy.objects.create(
        category=2,
        title='vip',
        price=50,
        project_num = 20,
        project_member = 40,
        project_space = 100,
        per_file_size = 20
    )

    models.PricePolicy.objects.create(
        category=2,
        title='svip',
        price=100,
        project_num = 50,
        project_member = 200,
        project_space = 1500,
        per_file_size = 50
    )

    models.PricePolicy.objects.create(
        category=2,
        title='ssvip',
        price=200,
        project_num = 200,
        project_member = 500,
        project_space = 3000,
        per_file_size = 100
    )

if __name__ == '__main__':
    run()

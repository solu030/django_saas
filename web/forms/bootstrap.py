from django import forms

class BootstrapForm(forms.Form):
    bootstrap_exclude_field = []
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in self.bootstrap_exclude_field:
                continue
            old_class = field.widget.attrs.get('class')
            field.widget.attrs['class'] = '{} form-control'.format(old_class)
            field.widget.attrs['placeholder'] = "请输入" + field.label

class BootstrapModelForm(forms.ModelForm):
    bootstrap_exclude_field = []
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in self.bootstrap_exclude_field:
                continue
            old_class = field.widget.attrs.get('class')
            field.widget.attrs['class'] = '{} form-control'.format(old_class)
            field.widget.attrs['placeholder'] = "请输入" + field.label
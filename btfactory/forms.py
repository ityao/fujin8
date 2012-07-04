from django import forms


# I put this on all required fields, because it's easier to pick up
# on them with CSS or JavaScript if they have a class of "required"
# in the HTML. Your mileage may vary. If/when Django ticket #3515
# lands in trunk, this will no longer be necessary.
attrs_dict = {'class': 'required'}


class ActressSearchForm(forms.Form):
    actress = forms.CharField(max_length=30)
    pageIndex = forms.DecimalField


class CreateActressForm(forms.Form):
    name = forms.CharField(max_length=20, required=True)
    header = forms.FileField(required=True)
    conames = forms.CharField(max_length=50, required=False)
    profile = forms.CharField(max_length=500, required=False, widget=forms.Textarea)


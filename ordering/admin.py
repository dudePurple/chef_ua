from django.contrib import admin
from django import forms
from .models import Product, Order


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'


class OrderAdmin(admin.ModelAdmin):
    form = OrderAdminForm

    def get_form(self, request, obj=None, **kwargs):
        """
        Implements restriction on transition between statuses
        """
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.status == 'pending':
            form.base_fields['status'].choices = [('pending', 'Pending'), ('active', 'Active')]
        elif obj and obj.status == 'active':
            form.base_fields['status'].choices = [('active', 'Active'), ('completed', 'Completed')]
        elif obj:
            form.base_fields['status'].choices = [('completed', 'Completed')]
        else:
            form.base_fields['status'].choices = [('pending', 'Pending')]

        return form


admin.site.register(Product)
admin.site.register(Order, OrderAdmin)

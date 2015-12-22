from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse_lazy
from .models import Party, Parcel


def index(request):
    return render(request, 'tutelary_example/index.html', {})


class PartyList(ListView):
    model = Party


class PartyDetail(DetailView):
    model = Party


class PartyCreate(CreateView):
    model = Party
    fields = ['name', 'address', 'status']


class PartyUpdate(UpdateView):
    model = Party
    fields = ['name', 'address', 'status']
    template_name_suffix = '_update_form'


class PartyDelete(DeleteView):
    model = Party
    success_url = reverse_lazy('party-list')


class ParcelList(ListView):
    model = Parcel


class ParcelDetail(DetailView):
    model = Parcel


class ParcelCreate(CreateView):
    model = Parcel
    fields = ['address', 'status']


class ParcelUpdate(UpdateView):
    model = Parcel
    fields = ['address', 'status']
    template_name_suffix = '_update_form'


class ParcelDelete(DeleteView):
    model = Parcel
    success_url = reverse_lazy('parcel-list')

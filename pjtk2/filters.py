from django import forms
from django.db import models
import django_filters

from pjtk2.models import Project, ProjectType, SamplePoint
from common.models import Lake

# from crispy_forms.helper import FormHelper
# from crispy_forms.layout import Layout, Field, Submit


class ValueInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    pass


def get_year_choices():
    """a little helper function to get a distinct list of years that can
    be used for the years filter.  The function returns a list of two
    element tuples.  the first tuple is an empty string and its
    indicator, the remaining tuples are each of the distinct years in
    Projects, sorted in reverse chronological order.
    """
    years = Project.objects.values_list("year")
    years = list(set([x[0] for x in years]))
    years.sort(reverse=True)
    years = [(x, x) for x in years]
    years.insert(0, ("", "---------"))
    return years


class ProjectFilter(django_filters.FilterSet):
    """A filter for project lists"""

    year = django_filters.NumberFilter()
    first_year = django_filters.NumberFilter("year", lookup_expr="gte")
    last_year = django_filters.NumberFilter("year", lookup_expr="lte")
    prj_cd = django_filters.CharFilter(lookup_expr="icontains")

    lake = ValueInFilter(field_name="lake__abbrev", lookup_expr="in")

    protocol = ValueInFilter(field_name="protocol__abbrev", lookup_expr="in")
    project_type = ValueInFilter(field_name="project_type__id", lookup_expr="in")
    scope = ValueInFilter(field_name="project_type__scope", lookup_expr="in")

    # scope protocol, project_type

    class Meta:
        model = Project
        # fields = ['year', 'project_type', 'lake', 'funding']
        fields = ["year", "project_type", "lake__abbrev", "protocol", "prj_cd"]


#    def __init__(self, *args, **kwargs):
#        # from https://github.com/alex/django-filter/issues/29
#        super(ProjectFilter, self).__init__(*args, **kwargs)
#        filter_ = self.filters["project_type"]
#
#        # this will grab all the fk ids that are in use
#        fk_counts = (
#            Project.objects.values_list("project_type")
#            .order_by("project_type")
#            .annotate(models.Count("project_type"))
#        )
#        ProjectType_ids = [fk for fk, cnt in fk_counts]
#        filter_.extra["queryset"] = ProjectType.objects.filter(pk__in=ProjectType_ids)
#
#    @property
#    def form(self):
#        self._form = super(ProjectFilter, self).form
#        self._form.helper = FormHelper()
#        self._form.helper.form_style = "inline"
#        self._form.helper.form_method = "get"
#        self._form.helper.form_action = ""
#
#        self._form.fields.update(
#            {
#                "year": forms.ChoiceField(
#                    label="Year:", choices=get_year_choices(), required=False
#                )
#            }
#        )
#
#        self._form.fields.update(
#            {
#                "lake": forms.ModelChoiceField(
#                    label="Lake:", queryset=Lake.objects.all(), required=False
#                )
#            }
#        )
#
#        self._form.fields.update(
#            {
#                "project_type": forms.ModelChoiceField(
#                    label="Project Type:",
#                    queryset=ProjectType.objects.all().order_by("project_type"),
#                    required=False,
#                )
#            }
#        )
#
#        self._form.helper.add_input(Submit("submit", "Apply Filter"))
#        self._form.helper.layout = Layout(
#            Field("year"),
#            Field("project_type"),
#            Field("lake"),
#            # Field('funding'),
#        )
#
#        return self._form
#


class SamplePointFilter(django_filters.FilterSet):
    """A filter for sample points lists"""

    year = django_filters.NumberFilter()
    first_year = django_filters.NumberFilter("project__year", lookup_expr="gte")
    last_year = django_filters.NumberFilter("project__year", lookup_expr="lte")

    lake = ValueInFilter(field_name="project__lake__abbrev", lookup_expr="in")

    project_type = django_filters.ModelMultipleChoiceFilter(
        "project__project_type",
        to_field_name="id",
        lookup_expr="in",
        queryset=ProjectType.objects.all(),
    )

    class Meta:
        model = SamplePoint
        fields = ["project__year", "project__project_type", "project__lake__abbrev"]
